from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.encar.client import EncarClient
from app.encar.parser import parse_car
from app.encar.query_builder import EncarQueryBuilder
from app.models import Filter, MonitorSettings, SeenCar, User, TelegramRecipient
from app.monitoring.deduplication import is_new_car
from app.telegram.notifications import TelegramNotifier


KOREA_TZ = ZoneInfo("Asia/Seoul")
MAX_VIEWS = 50


def matches_filter(car, filter_: Filter) -> bool:
    """Strict local validation so Telegram only receives matching cars."""

    if filter_.year_from is not None:
        if car.year is None or car.year < filter_.year_from:
            return False

    if filter_.year_to is not None:
        if car.year is None or car.year > filter_.year_to:
            return False

    if filter_.month_from is not None:
        if car.year is None:
            return False
        month_raw = None
        # Encar's raw Year is not retained by ParsedCar, so month filters
        # are currently enforced by Encar's query only.
        # Do not guess a month from the model year.
        month_raw = None
        if month_raw is None:
            return True

    if filter_.price_from is not None:
        if car.price is None or car.price < filter_.price_from:
            return False

    if filter_.price_to is not None:
        if car.price is None or car.price > filter_.price_to:
            return False

    if filter_.mileage_from is not None:
        if car.mileage is None or car.mileage < filter_.mileage_from:
            return False

    if filter_.mileage_to is not None:
        if car.mileage is None or car.mileage > filter_.mileage_to:
            return False

    return True


class EncarMonitor:

    def __init__(self, notifier: TelegramNotifier):
        self.encar_client = EncarClient()
        self.notifier = notifier

    async def check_filter(self, filter_: Filter) -> list:
        query = EncarQueryBuilder.build(filter_)

        print(
            f"[Monitor] Filter #{filter_.id}: "
            f"query={query}; "
            f"year={filter_.year_from}-{filter_.year_to}; "
            f"price={filter_.price_from}-{filter_.price_to}; "
            f"mileage={filter_.mileage_from}-{filter_.mileage_to}"
        )

        raw_cars = await self.encar_client.search(
            query=query,
            start=0,
            count=20,
        )

        new_cars = []
        db = SessionLocal()
        today_korea = datetime.now(KOREA_TZ).date()

        try:
            for raw_car in raw_cars:
                try:
                    details = await self.encar_client.get_vehicle_details(
                        int(raw_car["Id"])
                    )
                    car = parse_car(
                        raw_car,
                        details,
                    )
                except Exception as error:
                    print(
                        f"[Monitor] Failed to load Encar details "
                        f"for {raw_car.get('Id')}: {error}"
                    )
                    continue

                if not matches_filter(car, filter_):
                    print(
                        f"[Monitor] Skip {car.encar_id}: "
                        f"does not match filter "
                        f"(year={car.year}, price={car.price}, "
                        f"mileage={car.mileage})"
                    )
                    continue

                if car.first_advertised_at is None:
                    print(
                        f"[Monitor] Skip {car.encar_id}: "
                        f"no firstAdvertisedDateTime"
                    )
                    continue

                if car.first_advertised_at.date() != today_korea:
                    continue

                if car.view_count is None:
                    print(
                        f"[Monitor] Skip {car.encar_id}: "
                        f"no viewCount"
                    )
                    continue

                if car.view_count > MAX_VIEWS:
                    continue

                if is_new_car(
                    db,
                    filter_.id,
                    car.encar_id,
                ):
                    new_cars.append(car)
                    db.add(
                        SeenCar(
                            filter_id=filter_.id,
                            encar_id=car.encar_id,
                        )
                    )

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        if new_cars:
            recipient_db = SessionLocal()

            try:
                recipient_ids = recipient_db.scalars(
                    select(TelegramRecipient.telegram_id)
                    .order_by(TelegramRecipient.telegram_id)
                ).all()
            finally:
                recipient_db.close()

            if recipient_ids:
                for telegram_id in recipient_ids:
                    for car in new_cars:
                        try:
                            await self.notifier.send_car(
                                telegram_id=telegram_id,
                                car=car,
                            )
                        except Exception as error:
                            print(
                                f"[Monitor] Telegram notification failed "
                                f"for {telegram_id}: {error}"
                            )

                print(
                    f"[Monitor] Filter #{filter_.id}: "
                    f"sent {len(new_cars)} new cars to "
                    f"{len(recipient_ids)} Telegram recipient(s)"
                )
            else:
                print(
                    f"[Monitor] Filter #{filter_.id}: "
                    f"{len(new_cars)} new cars, but no Telegram recipients configured."
                )

        return new_cars

    async def check_user(self, user_id: int) -> int:
        db = SessionLocal()

        try:
            filters = db.scalars(
                select(Filter)
                .where(
                    Filter.user_id == user_id,
                    Filter.enabled.is_(True),
                )
                .order_by(Filter.id)
            ).all()

            total_new = 0

            for filter_ in filters:
                try:
                    new_cars = await self.check_filter(filter_)
                    total_new += len(new_cars)
                    print(
                        f"[Monitor] User #{user_id}, "
                        f"filter #{filter_.id} '{filter_.name}': "
                        f"{len(new_cars)} new cars"
                    )
                except Exception as error:
                    print(
                        f"[Monitor] User #{user_id}, "
                        f"filter #{filter_.id} error: {error}"
                    )

            return total_new
        finally:
            db.close()

    async def check_due_users(self):
        now = datetime.utcnow()
        db = SessionLocal()

        try:
            users = db.scalars(
                select(User).where(User.is_active.is_(True))
            ).all()

            existing_settings = {
                item.user_id
                for item in db.scalars(
                    select(MonitorSettings)
                ).all()
            }

            for user in users:
                if user.id not in existing_settings:
                    db.add(
                        MonitorSettings(
                            user_id=user.id,
                            enabled=True,
                            interval_minutes=settings.monitor_interval_minutes,
                            next_run_at=now,
                        )
                    )

            db.commit()

            due_settings = db.scalars(
                select(MonitorSettings)
                .where(
                    MonitorSettings.enabled.is_(True),
                    MonitorSettings.next_run_at.is_not(None),
                    MonitorSettings.next_run_at <= now,
                )
                .order_by(MonitorSettings.next_run_at)
            ).all()

            if not due_settings:
                return

            print(f"[Monitor] {len(due_settings)} user(s) due for scan.")

            for monitor_settings in due_settings:
                monitor_settings.last_run_at = now
                monitor_settings.next_run_at = (
                    now + timedelta(minutes=monitor_settings.interval_minutes)
                )
                db.commit()

                try:
                    total_new = await self.check_user(
                        monitor_settings.user_id
                    )
                    print(
                        f"[Monitor] User #{monitor_settings.user_id}: "
                        f"scan complete, {total_new} new cars."
                    )
                except Exception as error:
                    print(
                        f"[Monitor] User #{monitor_settings.user_id} "
                        f"scan failed: {error}"
                    )
        finally:
            db.close()

    async def close(self):
        await self.encar_client.close()
