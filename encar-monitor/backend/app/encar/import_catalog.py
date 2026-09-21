from __future__ import annotations

import asyncio
import json
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


def _add_model_name(value: object, result: list[str], seen: set[str]) -> None:
    if not isinstance(value, str):
        return

    name = " ".join(value.split()).strip()

    if not name or len(name) > 255:
        return

    # Служебные подписи, которые иногда встречаются в каталоге.
    if name.lower() in {"model", "models", "모델", "전체", "all"}:
        return

    if name not in seen:
        seen.add(name)
        result.append(name)


def _extract_models_from_json(
    payload: object,
) -> list[str]:
    """
    Encar иногда отдаёт каталог моделей как JSON, а не HTML.
    Структура ответа может меняться, поэтому разбираем несколько
    распространённых вариантов вместо привязки к одному JSON-пути.
    """

    result: list[str] = []
    seen: set[str] = set()

    model_keys = {
        "model",
        "modelname",
        "modelnm",
        "model_name",
        "modelnameko",
        "modelnmko",
    }

    def walk(value: object, in_model_context: bool = False) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_lower = str(key).lower().replace("-", "_")

                is_model_key = key_lower in model_keys
                child_context = (
                    in_model_context
                    or "model" in key_lower
                )

                if is_model_key:
                    if isinstance(child, str):
                        _add_model_name(
                            child,
                            result,
                            seen,
                        )
                    elif isinstance(child, list):
                        for item in child:
                            _add_model_name(
                                item,
                                result,
                                seen,
                            )

                # В структурах вида models -> [{name: ...}, ...]
                if (
                    in_model_context
                    and key_lower in {"name", "label", "title"}
                ):
                    _add_model_name(
                        child,
                        result,
                        seen,
                    )

                walk(
                    child,
                    child_context,
                )

        elif isinstance(value, list):
            for item in value:
                walk(item, in_model_context)

    walk(payload)

    return result


def parse_models(html: str) -> list[str]:
    """
    Разбирает каталог моделей Encar.

    Поддерживает два формата:
    1. JSON-ответ model.json;
    2. HTML со ссылками каталога.

    Это важно, потому что Encar может отдавать разные представления
    одного и того же каталога в зависимости от запроса/окружения.
    """

    # ---------------------------------------------------------
    # 1. JSON
    # ---------------------------------------------------------

    try:
        payload = json.loads(html)

        models = _extract_models_from_json(payload)

        if models:
            return models

    except (json.JSONDecodeError, TypeError):
        pass

    # ---------------------------------------------------------
    # 2. HTML fallback
    # ---------------------------------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    models: list[str] = []
    seen: set[str] = set()

    for link in soup.find_all("a"):
        href = str(link.get("href", ""))

        if "model" not in href.lower():
            continue

        _add_model_name(
            link.get_text(" ", strip=True),
            models,
            seen,
        )

    return models



async def fetch_models_from_search(
    encar_client,
    manufacturer_name: str,
    max_results: int = 5000,
    page_size: int = 500,
) -> list[str]:
    """Build the model catalog from Encar's real search API."""

    query = (
        f"(And.Hidden.N._.CarType.Y._."
        f"Manufacturer.{manufacturer_name}.)"
    )

    result: list[str] = []
    seen: set[str] = set()

    no_new_pages = 0

    for start in range(0, max_results, page_size):
        try:
            batch = await encar_client.search(
                query=query,
                start=start,
                count=page_size,
            )
        except Exception as error:
            print(f"  Search API error: {error}")
            break

        if not batch:
            break

        before_count = len(result)

        for car in batch:
            model_name = car.get("Model")

            if not isinstance(model_name, str):
                continue

            model_name = " ".join(model_name.split()).strip()

            if not model_name or len(model_name) > 255:
                continue

            if model_name not in seen:
                seen.add(model_name)
                result.append(model_name)

        if len(result) == before_count:
            no_new_pages += 1
        else:
            no_new_pages = 0

        # Если две страницы подряд не дали новых моделей,
        # дальше почти наверняка идут только дубликаты.
        if no_new_pages >= 2:
            break

        if len(batch) < page_size:
            break

    return result


async def fetch_models(
    http_client: httpx.AsyncClient,
    encar_client,
    manufacturer_name: str,
    manufacturer_code: str,
) -> list[str]:
    """Use the legacy catalog first, then the working Search API."""

    url = MODEL_URL.format(manufacturer_code)

    try:
        model_html = await get_page(http_client, url)
        models = parse_models(model_html)

        if models:
            return models

        print(
            "  Legacy catalog endpoint returned no models; "
            "falling back to Search API."
        )
    except Exception as error:
        print(f"  Legacy catalog endpoint error: {error}")

    return await fetch_models_from_search(
        encar_client,
        manufacturer_name,
    )


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
        from app.encar.client import EncarClient

        encar_client = EncarClient()

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

                    models = await fetch_models(
                        client,
                        encar_client,
                        name,
                        code,
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
            await encar_client.close()


if __name__ == "__main__":
    asyncio.run(import_catalog())