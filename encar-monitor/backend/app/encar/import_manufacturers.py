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

        start = 0

        while start < MAX_RESULTS:
            print(f"Запрашиваем объявления: {start} - {start + PAGE_SIZE}")

            query = "(And.Hidden.N._.CarType.Y.)"

            result = await client.search(
                query=query,
                start=start,
                count=PAGE_SIZE,
            )

            cars = result.get("SearchResults", [])

            if not cars:
                print("Объявления закончились.")
                break

            for car in cars:
                manufacturer = car.get("Manufacturer")

                if not manufacturer:
                    continue

                manufacturer = manufacturer.strip()

                if not manufacturer:
                    continue

                all_manufacturers[manufacturer] = (
                    all_manufacturers.get(manufacturer, 0) + 1
                )

            print(
                f"Получено: {len(cars)}, "
                f"уникальных марок: {len(all_manufacturers)}"
            )

            if len(cars) < PAGE_SIZE:
                print("Получена последняя страница.")
                break

            start += PAGE_SIZE

        print()
        print("=" * 60)
        print(f"Всего найдено уникальных марок: {len(all_manufacturers)}")
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

            for name, count in sorted(all_manufacturers.items()):
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