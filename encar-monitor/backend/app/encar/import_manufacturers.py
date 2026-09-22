from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.models import CatalogManufacturer
from app.encar.client import EncarClient


PAGE_SIZE = 500
MAX_RESULTS = 100_000


async def import_manufacturers() -> None:
    client = EncarClient()

    try:
        print("Начинаем импорт производителей из Encar...")

        all_manufacturers: dict[str, int] = {}

        # Encar separates domestic (Y) and imported (N) vehicles.
        # Import both sets so the catalog does not silently lose
        # manufacturers such as BMW, BYD, Toyota, Mercedes, etc.
        for car_type in ("Y", "N"):
            print()
            print(f"Импорт производителей: CarType.{car_type}")

            start = 0

            while start < MAX_RESULTS:
                print(
                    f"Запрашиваем объявления: "
                    f"{start} - {start + PAGE_SIZE}"
                )

                query = (
                    f"(And.Hidden.N._.CarType.{car_type}.)"
                )

                cars = await client.search(
                    query=query,
                    start=start,
                    count=PAGE_SIZE,
                )

                if not cars:
                    print("Объявления закончились.")
                    break

                for car in cars:
                    manufacturer = car.get("Manufacturer")

                    if not manufacturer:
                        continue

                    manufacturer = str(
                        manufacturer
                    ).strip()

                    if not manufacturer:
                        continue

                    all_manufacturers[manufacturer] = (
                        all_manufacturers.get(
                            manufacturer,
                            0,
                        )
                        + 1
                    )

                print(
                    f"Получено: {len(cars)}, "
                    f"уникальных марок: "
                    f"{len(all_manufacturers)}"
                )

                if len(cars) < PAGE_SIZE:
                    print("Получена последняя страница.")
                    break

                start += PAGE_SIZE

        print()
        print("=" * 60)
        print(
            "Всего найдено уникальных марок: "
            f"{len(all_manufacturers)}"
        )
        print("=" * 60)

        db = SessionLocal()

        try:
            existing = {
                manufacturer.name: manufacturer
                for manufacturer in db.scalars(
                    select(CatalogManufacturer)
                ).all()
            }

            added = 0
            updated = 0

            for name, count in sorted(
                all_manufacturers.items()
            ):
                manufacturer = existing.get(name)

                if manufacturer:
                    manufacturer.count = count
                    updated += 1
                else:
                    manufacturer = CatalogManufacturer(
                        name=name,
                        label=name,
                        count=count,
                    )

                    db.add(manufacturer)
                    added += 1

            db.commit()

            print()
            print(f"Добавлено новых марок: {added}")
            print(f"Обновлено марок: {updated}")

        finally:
            db.close()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(import_manufacturers())
