from app.models import Filter


class EncarQueryBuilder:

    @staticmethod
    def build(filter_: Filter) -> str:
        """Build an Encar search query from the saved filter."""

        leaf_conditions: list[str] = []

        if filter_.badge:
            leaf_conditions.append(
                f"Badge.{filter_.badge}"
            )

        if filter_.fuel_type:
            leaf_conditions.append(
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
            leaf_conditions.append(
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
            leaf_conditions.append(
                f"Mileage.{mileage_from}_{mileage_to}"
            )

        conditions = []

        if filter_.manufacturer:
            conditions.append(
                f"Manufacturer.{filter_.manufacturer}"
            )

        if filter_.model:
            conditions.append(
                f"Model.{filter_.model}"
            )

        conditions.extend(leaf_conditions)

        if conditions:
            condition = (
                f"CarType.N._."
                f"{'._.'.join(conditions)}."
            )
        else:
            condition = "CarType.N."

        return f"(And.Hidden.N._.(C.{condition}))"
