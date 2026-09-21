from __future__ import annotations

import asyncio
import re

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    CatalogManufacturer,
    CatalogModel,
)


COMPANY_URL = "https://m.encar.com/pr/company.json?method=carList"
MODEL_URL = "https://m.encar.com/pr/model.json?carType=for&method=carList&mnfccd={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


async def get_page(
    client: httpx.AsyncClient,
    url: str,
) -> str:
    response = await client.get(url)

    response.raise_for_status()

    return response.text


def parse_manufacturers(html: str) -> list[dict]:
    """
    Получает производителей со страницы Encar.

    Возвращает:

    [
        {
            "name": "BMW",
            "label": "BMW",
            "code": "012"
        },
        ...
    ]
    """

    soup = BeautifulSoup(html, "html.parser")

    manufacturers = []

    # Ищем ссылки вида:
    #
    # /pr/model.json?carType=for&method=carList&mnfccd=012
    #
    for link in soup.find_all("a"):
        href = link.get("href")

        if not href:
            continue

        match = re.search(r"mnfccd=(\d+)", href)

        if not match:
            continue

        code = match.group(1)

        name = link.get_text(" ", strip=True)

        if not name:
            continue

        manufacturers.append(
            {
                "name": name,
                "label": name,
                "code": code,
            }
        )

    # Убираем дубликаты по коду производителя
    unique = {}

    for manufacturer in manufacturers:
        unique[manufacturer["code"]] = manufacturer

    return list(unique.values())


def parse_models(html: str) -> list[str]:
    """
    Получает список моделей со страницы конкретного производителя.
    """

    soup = BeautifulSoup(html, "html.parser")

    models = []

    for link in soup.find_all("a"):
        name = link.get_text(" ", strip=True)

        if not name:
            continue

        # На странице моделей названия находятся
        # в ссылках каталога.
        #
        # Отбрасываем служебные ссылки.
        href = link.get("href", "")

        if "model" not in href.lower():
            continue

        models.append(name)

    # Уникальные модели
    result = []
    seen = set()

    for model in models:
        if model in seen:
            continue

        seen.add(model)
        result.append(model)

    return result


async def import_catalog() -> None:
    print()
    print("=" * 70)
    print("EN CAR CATALOG IMPORT")
    print("=" * 70)
    print()

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=30,
        follow_redirects=True,
    ) as client:

        # ---------------------------------------------------------
        # 1. Получаем производителей
        # ---------------------------------------------------------

        print("Получаем список производителей...")

        html = await get_page(
            client,
            COMPANY_URL,
        )

        manufacturers = parse_manufacturers(html)

        print(
            f"Найдено производителей: {len(manufacturers)}"
        )

        if not manufacturers:
            print()
            print("Производители не найдены.")
            print("HTML Encar мог измениться.")
            return

        # ---------------------------------------------------------
        # 2. Подключаемся к БД
        # ---------------------------------------------------------

        db = SessionLocal()

        try:

            # -----------------------------------------------------
            # 3. Импортируем производителей
            # -----------------------------------------------------

            manufacturer_db = {}

            for item in manufacturers:

                name = item["name"]

                manufacturer = db.scalar(
                    select(CatalogManufacturer).where(
                        CatalogManufacturer.name == name
                    )
                )

                if manufacturer is None:

                    manufacturer = CatalogManufacturer(
                        name=name,
                        label=item["label"],
                        count=None,
                    )

                    db.add(manufacturer)
                    db.flush()

                manufacturer_db[item["code"]] = manufacturer

            db.commit()

            print(
                f"Производители сохранены в SQLite: "
                f"{len(manufacturer_db)}"
            )

            print()

            # -----------------------------------------------------
            # 4. Получаем модели каждого производителя
            # -----------------------------------------------------

            total_models = 0

            for index, item in enumerate(
                manufacturers,
                start=1,
            ):

                code = item["code"]
                name = item["name"]

                print(
                    f"[{index}/{len(manufacturers)}] "
                    f"{name} ({code})"
                )

                url = MODEL_URL.format(code)

                try:

                    model_html = await get_page(
                        client,
                        url,
                    )

                    models = parse_models(
                        model_html
                    )

                except Exception as error:

                    print(
                        f"  Ошибка загрузки моделей: {error}"
                    )

                    continue

                print(
                    f"  Найдено моделей: {len(models)}"
                )

                manufacturer = manufacturer_db[code]

                # -------------------------------------------------
                # Сохраняем модели
                # -------------------------------------------------

                existing_models = {
                    model.name
                    for model in db.scalars(
                        select(CatalogModel).where(
                            CatalogModel.manufacturer_id
                            == manufacturer.id
                        )
                    ).all()
                }

                added = 0

                for model_name in models:

                    if model_name in existing_models:
                        continue

                    model = CatalogModel(
                        manufacturer_id=manufacturer.id,
                        name=model_name,
                        count=None,
                    )

                    db.add(model)

                    added += 1
                    total_models += 1

                db.commit()

                print(
                    f"  Добавлено новых моделей: {added}"
                )

                # Небольшая пауза между запросами
                await asyncio.sleep(0.2)

            print()
            print("=" * 70)
            print("ИМПОРТ ЗАВЕРШЁН")
            print("=" * 70)
            print(
                f"Производителей: {len(manufacturers)}"
            )
            print(
                f"Новых моделей: {total_models}"
            )
            print("=" * 70)

        finally:
            db.close()


if __name__ == "__main__":
    asyncio.run(import_catalog())