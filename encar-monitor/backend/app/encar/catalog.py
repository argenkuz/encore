from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CatalogManufacturer,
    CatalogModel,
    CatalogBadge,
)

from app.encar.client import EncarClient


PAGE_SIZE = 500
MAX_RESULTS = 5000


class CatalogService:

    def __init__(self):
        self.client = EncarClient()

        # RAM cache
        self._manufacturers_cache: list[dict] | None = None

        self._models_cache: dict[
            str,
            list[dict],
        ] = {}

        self._badges_cache: dict[
            tuple[str, str],
            list[dict],
        ] = {}


    # =====================================================
    # MANUFACTURERS
    # =====================================================

    def get_manufacturers(
        self,
        db: Session,
    ) -> list[dict]:

        # 1. RAM
        if self._manufacturers_cache is not None:
            return self._manufacturers_cache


        # 2. SQLite
        manufacturers = db.scalars(
            select(CatalogManufacturer)
            .order_by(
                CatalogManufacturer.name
            )
        ).all()


        self._manufacturers_cache = [
            {
                "id": manufacturer.id,
                "name": manufacturer.name,
                "label": manufacturer.label,
                "count": manufacturer.count,
            }
            for manufacturer in manufacturers
        ]


        return self._manufacturers_cache


    # =====================================================
    # MODELS
    # =====================================================

    async def get_models(
        self,
        manufacturer: str,
        db: Session,
    ) -> list[dict]:

        manufacturer = manufacturer.strip()


        if not manufacturer:
            return []


        # -------------------------------------------------
        # 1. RAM CACHE
        # -------------------------------------------------

        if manufacturer in self._models_cache:

            return self._models_cache[
                manufacturer
            ]


        # -------------------------------------------------
        # 2. FIND MANUFACTURER
        # -------------------------------------------------

        manufacturer_row = db.scalar(
            select(CatalogManufacturer)
            .where(
                CatalogManufacturer.name
                == manufacturer
            )
        )


        if not manufacturer_row:
            return []


        # -------------------------------------------------
        # 3. SQLITE
        # -------------------------------------------------

        models = db.scalars(
            select(CatalogModel)
            .where(
                CatalogModel.manufacturer_id
                == manufacturer_row.id
            )
            .order_by(
                CatalogModel.name
            )
        ).all()


        if models:

            result = [
                {
                    "id": model.id,
                    "name": model.name,
                    "count": model.count,
                }
                for model in models
            ]


            self._models_cache[
                manufacturer
            ] = result


            return result


        # -------------------------------------------------
        # 4. ENCAR
        # -------------------------------------------------

        query = (
            f"(And.Hidden.N._.(C.CarType.N._."
            f"Manufacturer.{manufacturer}.))"
        )


        print(
            f"Loading models from Encar: "
            f"{manufacturer}"
        )

        print(
            f"Encar query: {query}"
        )


        raw_results: list[dict] = []


        for start in range(
            0,
            MAX_RESULTS,
            PAGE_SIZE,
        ):

            batch = await self.client.search(
                query=query,
                start=start,
                count=PAGE_SIZE,
            )


            if not batch:
                break


            raw_results.extend(batch)


            if len(batch) < PAGE_SIZE:
                break


        # -------------------------------------------------
        # 5. BUILD MODEL COUNTS
        # -------------------------------------------------

        model_counts: dict[
            str,
            int,
        ] = {}


        for car in raw_results:

            model_name = car.get(
                "Model"
            )


            if not model_name:
                continue


            model_name = str(
                model_name
            ).strip()


            if not model_name:
                continue


            model_counts[
                model_name
            ] = (
                model_counts.get(
                    model_name,
                    0,
                )
                + 1
            )


        # -------------------------------------------------
        # 6. SAVE TO SQLITE
        # -------------------------------------------------

        result: list[dict] = []


        for name, count in sorted(
            model_counts.items(),
            key=lambda item: item[0],
        ):

            model = CatalogModel(
                manufacturer_id=(
                    manufacturer_row.id
                ),
                name=name,
                count=count,
            )


            db.add(model)

            db.flush()


            result.append(
                {
                    "id": model.id,
                    "name": model.name,
                    "count": model.count,
                }
            )


        db.commit()


        # -------------------------------------------------
        # 7. RAM CACHE
        # -------------------------------------------------

        self._models_cache[
            manufacturer
        ] = result


        return result


    # =====================================================
    # BADGES
    # =====================================================

    async def get_badges(
        self,
        manufacturer: str,
        model: str,
        db: Session,
    ) -> list[dict]:

        manufacturer = manufacturer.strip()
        model = model.strip()


        if not manufacturer or not model:
            return []


        cache_key = (
            manufacturer,
            model,
        )


        # -------------------------------------------------
        # 1. RAM CACHE
        # -------------------------------------------------

        if cache_key in self._badges_cache:

            return self._badges_cache[
                cache_key
            ]


        # -------------------------------------------------
        # 2. FIND MANUFACTURER
        # -------------------------------------------------

        manufacturer_row = db.scalar(
            select(CatalogManufacturer)
            .where(
                CatalogManufacturer.name
                == manufacturer
            )
        )


        if not manufacturer_row:
            return []


        # -------------------------------------------------
        # 3. FIND MODEL
        # -------------------------------------------------

        model_row = db.scalar(
            select(CatalogModel)
            .where(
                CatalogModel.manufacturer_id
                == manufacturer_row.id,
                CatalogModel.name
                == model,
            )
        )


        if not model_row:
            return []


        # -------------------------------------------------
        # 4. SQLITE
        # -------------------------------------------------

        badges = db.scalars(
            select(CatalogBadge)
            .where(
                CatalogBadge.model_id
                == model_row.id
            )
            .order_by(
                CatalogBadge.name
            )
        ).all()


        if badges:

            result = [
                {
                    "id": badge.id,
                    "name": badge.name,
                    "count": badge.count,
                }
                for badge in badges
            ]


            self._badges_cache[
                cache_key
            ] = result


            return result


        # -------------------------------------------------
        # 5. ENCAR
        # -------------------------------------------------

        query = (
            f"(And.Hidden.N._.(C.CarType.N._."
            f"Manufacturer.{manufacturer}._."
            f"Model.{model}.))"
        )


        print(
            f"Loading badges from Encar: "
            f"{manufacturer} / {model}"
        )

        print(
            f"Encar query: {query}"
        )


        raw_results: list[dict] = []


        for start in range(
            0,
            MAX_RESULTS,
            PAGE_SIZE,
        ):

            batch = await self.client.search(
                query=query,
                start=start,
                count=PAGE_SIZE,
            )


            if not batch:
                break


            raw_results.extend(batch)


            if len(batch) < PAGE_SIZE:
                break


        # -------------------------------------------------
        # 6. BUILD BADGE COUNTS
        # -------------------------------------------------

        badge_counts: dict[
            str,
            int,
        ] = {}


        for car in raw_results:

            badge_name = car.get(
                "Badge"
            )


            if not badge_name:
                continue


            badge_name = str(
                badge_name
            ).strip()


            if not badge_name:
                continue


            badge_counts[
                badge_name
            ] = (
                badge_counts.get(
                    badge_name,
                    0,
                )
                + 1
            )


        # -------------------------------------------------
        # 7. SAVE TO SQLITE
        # -------------------------------------------------

        result: list[dict] = []


        for name, count in sorted(
            badge_counts.items(),
            key=lambda item: item[0],
        ):

            badge = CatalogBadge(
                model_id=model_row.id,
                name=name,
                count=count,
            )


            db.add(badge)

            db.flush()


            result.append(
                {
                    "id": badge.id,
                    "name": badge.name,
                    "count": badge.count,
                }
            )


        db.commit()


        # -------------------------------------------------
        # 8. RAM CACHE
        # -------------------------------------------------

        self._badges_cache[
            cache_key
        ] = result


        return result


    # =====================================================
    # CACHE
    # =====================================================

    def invalidate_manufacturers_cache(
        self,
    ):

        self._manufacturers_cache = None


    def invalidate_models_cache(
        self,
        manufacturer: str | None = None,
    ):

        if manufacturer is None:

            self._models_cache.clear()

        else:

            self._models_cache.pop(
                manufacturer,
                None,
            )


    def invalidate_badges_cache(
        self,
        manufacturer: str | None = None,
        model: str | None = None,
    ):

        if (
            manufacturer is None
            or model is None
        ):

            self._badges_cache.clear()

            return


        self._badges_cache.pop(
            (
                manufacturer,
                model,
            ),
            None,
        )


    # =====================================================
    # CHECK
    # =====================================================

    def has_manufacturers(
        self,
        db: Session,
    ) -> bool:

        manufacturer = db.scalar(
            select(
                CatalogManufacturer.id
            ).limit(1)
        )


        return manufacturer is not None


    # =====================================================
    # CLOSE
    # =====================================================

    async def close(self):

        await self.client.close()