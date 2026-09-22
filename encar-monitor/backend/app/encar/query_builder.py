from app.encar.car_type import get_car_type
from app.models import Filter


class EncarQueryBuilder:

    @staticmethod
    def build(filter_: Filter) -> str:
        """Build Encar's general search query for domestic/imported cars."""

        conditions: list[str] = []

        if filter_.manufacturer:
            conditions.append(
                f"Manufacturer.{filter_.manufacturer}"
            )

        if filter_.model:
            conditions.append(
                f"Model.{filter_.model}"
            )

        if filter_.badge:
            conditions.append(
                f"Badge.{filter_.badge}"
            )

        if filter_.fuel_type:
            conditions.append(
                f"FuelType.{filter_.fuel_type}"
            )

        if (
            filter_.price_from is not None
            or filter_.price_to is not None
        ):
            price_from = (
                filter_.price_from
                if filter_.price_from is not None
                else 0
            )
            price_to = (
                filter_.price_to
                if filter_.price_to is not None
                else 999999
            )
            conditions.append(
                f"Price.{price_from}_{price_to}"
            )

        if (
            filter_.mileage_from is not None
            or filter_.mileage_to is not None
        ):
            mileage_from = (
                filter_.mileage_from
                if filter_.mileage_from is not None
                else 0
            )
            mileage_to = (
                filter_.mileage_to
                if filter_.mileage_to is not None
                else 999999
            )
            conditions.append(
                f"Mileage.{mileage_from}_{mileage_to}"
            )

        car_type = get_car_type(filter_.manufacturer)

        if conditions:
            condition = "._.".join(conditions)
            return f"(And.Hidden.N._.CarType.{car_type}._.{condition}.)"

        return f"(And.Hidden.N._.CarType.{car_type}.)"
