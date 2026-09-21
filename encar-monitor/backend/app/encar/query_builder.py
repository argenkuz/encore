from app.models import Filter


class EncarQueryBuilder:

    @staticmethod
    def build(filter_: Filter) -> str:
        """Build Encar's hierarchical search query.

        Verified Encar web-search examples use nested C groups for
        Manufacturer -> Model. Leaf filters remain inside the selected
        model group.
        """

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

        if filter_.model and filter_.manufacturer:
            model_conditions = [
                f"Model.{filter_.model}",
                *leaf_conditions,
            ]
            model_group = "._.".join(model_conditions)

            manufacturer_group = (
                f"Manufacturer.{filter_.manufacturer}._."
                f"(C.{model_group}.)"
            )

            condition = (
                f"CarType.N._."
                f"{manufacturer_group}."
            )

        elif filter_.manufacturer:
            manufacturer_conditions = [
                f"Manufacturer.{filter_.manufacturer}",
                *leaf_conditions,
            ]

            condition = (
                f"CarType.N._."
                f"{'._.'.join(manufacturer_conditions)}."
            )

        elif leaf_conditions:
            condition = (
                f"CarType.N._."
                f"{'._.'.join(leaf_conditions)}."
            )

        else:
            condition = "CarType.N."

        return f"(And.Hidden.N._.(C.{condition}))"
