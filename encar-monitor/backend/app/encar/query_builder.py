from app.models import Filter


class EncarQueryBuilder:

    @staticmethod
    def build(filter_: Filter) -> str:
        """Build a query using Encar's hierarchical C.* grammar.

        Encar's web search examples nest Manufacturer -> Model.
        This is important for model names containing parentheses such
        as "M5 (G90)" and "X7 (G07)".
        """

        # Build the inner conditions first.
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

        # Encar's hierarchy:
        # CarType -> Manufacturer -> Model -> leaf filters.
        if filter_.model:
            model_inner = [
                f"Model.{filter_.model}"
            ]

            if leaf_conditions:
                model_inner.extend(leaf_conditions)

            model_group = "._.".join(model_inner)

            manufacturer_inner = (
                f"Manufacturer.{filter_.manufacturer}._."
                f"(C.{model_group}.)"
            )
        elif filter_.manufacturer:
            manufacturer_inner = (
                f"Manufacturer.{filter_.manufacturer}"
            )
            if not leaf_conditions:
                manufacturer_inner = manufacturer_inner
            else:
                manufacturer_inner += (
                    "._."
                    + "._.".join(leaf_conditions)
                )
        else:
            manufacturer_inner = " ".join(leaf_conditions)

        if filter_.manufacturer or filter_.model:
            condition = (
                f"CarType.N._."
                f"{manufacturer_inner}."
            )
        else:
            condition = f"CarType.N._.{manufacturer_inner}."

        return f"(And.Hidden.N._.(C.{condition}))"
