import asyncio
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
SEARCH_PAGE_SIZE = 50
DETAIL_CONCURRENCY = 5


def matches_filter(car, filter_: Filter) -> bool:
    """Strict local validation before a car can be sent to Telegram."""

    # Treat year/month as one calendar range.
    #
    # Examples:
    #   11.2019 -> 2023       = 2019-11 through 2023-12
    #   2020    -> 2023       = 2020-01 through 2023-12
    #   2020-03 -> 2022-08    = 2020-03 through 2022-08
    if (
        filter_.year_from is not None
        or filter_.month_from is not None
        or filter_.year_to is not None
        or filter_.month_to is not None
    ):
        if car.year is None:
            return False

        if car.month is None:
            return False

        car_yyyymm = car.year * 100 + car.month

        start_yyyymm = None
        if filter_.year_from is not None:
            start_month = (
                filter_.month_from
                if filter_.month_from is not None
                else 1
            )
            start_yyyymm = filter_.year_from * 100 + start_month

        end_yyyymm = None
        if filter_.year_to is not None:
            end_month = (
                filter_.month_to
                if filter_.month_to is not None
                else 12
            )
            end_yyyymm = filter_.year_to * 100 + end_month

        if start_yyyymm is not None and car_yyyymm < start_yyyymm:
            return False

        if end_yyyymm is not None and car_yyyymm > end_yyyymm:
            return False

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

    async def _load_new_details(
        self,
        raw_cars: list[dict],
        filter_id: int,
        db,
    ) -> list:
        """Load details only for cars not already seen by this filter."""
        if not raw_cars:
            return []

        raw_ids = []
        for raw_car in raw_cars:
            try:
                raw_ids.append(int(raw_car["Id"]))
            except (KeyError, TypeError, ValueError):
                continue

        if not raw_ids:
            return []

        seen_ids = set(
            db.scalars(
                select(SeenCar.encar_id).where(
                    SeenCar.filter_id == filter_id,
                    SeenCar.encar_id.in_(raw_ids),
                )
            ).all()
        )

        candidates = [
            raw_car
            for raw_car in raw_cars
            if int(raw_car.get("Id", 0) or 0) not in seen_ids
        ]

        semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

        async def load_one(raw_car: dict):
            async with semaphore:
                try:
                    details = await self.encar_client.get_vehicle_details(
                        int(raw_car["Id"])
                    )
                    return parse_car(raw_car, details)
                except Exception as error:
                    print(
                        f"[Monitor] Failed to load Encar details "
                        f"for {raw_car.get('Id')}: {error}"
                    )
                    return None

        parsed = await asyncio.gather(
            *(load_one(raw_car) for raw_car in candidates)
        )
        return [car for car in parsed if car is not None]

    async def check_filter(self, filter_: Filter) -> list:
        query = EncarQueryBuilder.build(filter_)

        print(
            f"[Monitor] Filter #{filter_.id}: "
            f"query={query}; "
            f"year={filter_.year_from}-{filter_.year_to}; "
            f"month={filter_.month_from}-{filter_.month_to}; "
            f"price={filter_.price_from}-{filter_.price_to}; "
            f"mileage={filter_.mileage_from}-{filter_.mileage_to}"
        )

        db = SessionLocal()
        today_korea = datetime.now(KOREA_TZ).date()
        candidates = []

        try:
            start = 0
            total_catalog = None
            pages = 0

            while True:
                page = await self.encar_client.search_page(
                    query=query,
                    start=start,
                    count=SEARCH_PAGE_SIZE,
                )
                raw_cars = page["results"]
                total_catalog = page["total"]
                pages += 1

                if not raw_cars:
                    break

                print(
                    f"[Monitor] Filter #{filter_.id}: "
                    f"page={pages}, start={start}, "
                    f"received={len(raw_cars)}, total={total_catalog}"
                )

                cars = await self._load_new_details(
                    raw_cars=raw_cars,
                    filter_id=filter_.id,
                    db=db,
                )

                for car in cars:
                    if not matches_filter(car, filter_):
                        print(
                            f"[Monitor] Skip {car.encar_id}: "
                            f"does not match filter "
                            f"(year={car.year}, month={car.month}, "
                            f"price={car.price}, mileage={car.mileage})"
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

                    candidates.append(car)

                start += len(raw_cars)

                # Stop only after the actual last page. We do not stop on
                # "old" firstAdvertisedDateTime because the API is ordered
                # by ModifiedDate, not by first advertisement date.
                if len(raw_cars) < SEARCH_PAGE_SIZE:
                    break

            print(
                f"[Monitor] Filter #{filter_.id}: "
                f"catalog scan complete, pages={pages}, "
                f"total={total_catalog}, candidates={len(candidates)}"
            )

        finally:
            db.close()

        if not candidates:
            return []

        recipient_db = SessionLocal()
        try:
            recipient_ids = recipient_db.scalars(
                select(TelegramRecipient.telegram_id).order_by(
                    TelegramRecipient.telegram_id
                )
            ).all()
        finally:
            recipient_db.close()

        if not recipient_ids:
            print(
                f"[Monitor] Filter #{filter_.id}: "
                f"{len(candidates)} candidates, but no Telegram recipients configured."
            )
            return []

        notified = []

        for car in candidates:
            delivered_to_all = True

            for telegram_id in recipient_ids:
                try:
                    await self.notifier.send_car(
                        telegram_id=telegram_id,
                        car=car,
                    )
                except Exception as error:
                    delivered_to_all = False
                    print(
                        f"[Monitor] Telegram notification failed "
                        f"for {telegram_id}, car {car.encar_id}: {error}"
                    )

            if delivered_to_all:
                notified.append(car)

                db = SessionLocal()
                try:
                    if is_new_car(
                        db,
                        filter_.id,
                        car.encar_id,
                    ):
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
            else:
                print(
                    f"[Monitor] Car {car.encar_id} remains retryable "
                    f"because at least one Telegram delivery failed."
                )

        print(
            f"[Monitor] Filter #{filter_.id}: "
            f"notified {len(notified)} of {len(candidates)} candidate(s) "
            f"to {len(recipient_ids)} Telegram recipient(s)"
        )

        return notified

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
