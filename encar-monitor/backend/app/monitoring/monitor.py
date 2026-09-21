from sqlalchemy import select

from app.database import SessionLocal
from app.encar.client import EncarClient
from app.encar.parser import parse_car
from app.encar.query_builder import EncarQueryBuilder
from app.models import Filter, SeenCar
from app.monitoring.deduplication import is_new_car
from app.telegram.notifications import TelegramNotifier


class EncarMonitor:

    def __init__(
        self,
        notifier: TelegramNotifier,
    ):
        self.encar_client = EncarClient()
        self.notifier = notifier

    async def check_filter(
        self,
        filter_: Filter,
    ) -> list:

        query = EncarQueryBuilder.build(
            filter_
        )

        data = await self.encar_client.search(
            query=query,
            start=0,
            count=20,
        )

        raw_cars = data.get(
            "SearchResults",
            [],
        )

        new_cars = []

        db = SessionLocal()

        try:
            for raw_car in raw_cars:

                car = parse_car(raw_car)

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

        for car in new_cars:

            await self.notifier.send_car(
                telegram_id=filter_.user.telegram_id,
                car=car,
            )

        return new_cars

    async def check_all_filters(self):

        db = SessionLocal()

        try:
            filters = db.scalars(
                select(Filter)
                .where(
                    Filter.enabled.is_(True)
                )
            ).all()

            print(
                f"Checking "
                f"{len(filters)} active filters..."
            )

            for filter_ in filters:

                try:

                    new_cars = await self.check_filter(
                        filter_
                    )

                    print(
                        f"Filter #{filter_.id} "
                        f"'{filter_.name}': "
                        f"{len(new_cars)} new cars"
                    )

                except Exception as error:

                    print(
                        f"Filter #{filter_.id} "
                        f"error: {error}"
                    )

        finally:
            db.close()

    async def close(self):

        await self.encar_client.close()