from datetime import datetime, timedelta

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.encar.client import EncarClient
from app.encar.parser import parse_car
from app.encar.query_builder import EncarQueryBuilder
from app.models import Filter, MonitorSettings, SeenCar, User
from app.monitoring.deduplication import is_new_car
from app.telegram.notifications import TelegramNotifier


class EncarMonitor:

    def __init__(self, notifier: TelegramNotifier):
        self.encar_client = EncarClient()
        self.notifier = notifier

    async def check_filter(self, filter_: Filter) -> list:
        query = EncarQueryBuilder.build(filter_)

        data = await self.encar_client.search(
            query=query,
            start=0,
            count=20,
        )

        raw_cars = data.get("SearchResults", [])
        new_cars = []
        db = SessionLocal()

        try:
            for raw_car in raw_cars:
                car = parse_car(raw_car)

                if is_new_car(db, filter_.id, car.encar_id):
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

        for car in new_cars:
            await self.notifier.send_car(
                telegram_id=filter_.user.telegram_id,
                car=car,
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
            # Backfill settings for users created before the settings table
            # existed, so existing deployments keep monitoring automatically.
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
