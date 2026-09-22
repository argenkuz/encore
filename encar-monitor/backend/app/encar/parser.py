from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedCar:
    encar_id: int
    manufacturer: str | None
    model: str | None
    badge: str | None
    year: int | None
    mileage: int | None
    price: int | None
    fuel_type: str | None
    region: str | None
    photo: str | None
    encar_url: str
    first_advertised_at: datetime | None
    view_count: int | None


def parse_car(
    data: dict,
    details: dict | None = None,
) -> ParsedCar:
    encar_id = int(data["Id"])

    year_raw = data.get("Year")
    mileage_raw = data.get("Mileage")
    price_raw = data.get("Price")

    manage = (details or {}).get("manage") or {}

    first_advertised_raw = manage.get(
        "firstAdvertisedDateTime"
    )
    first_advertised_at = None

    if first_advertised_raw:
        try:
            first_advertised_at = datetime.fromisoformat(
                first_advertised_raw
            )
        except ValueError:
            pass

    view_count_raw = manage.get("viewCount")
    view_count = (
        int(view_count_raw)
        if view_count_raw is not None
        else None
    )

    return ParsedCar(
        encar_id=encar_id,
        manufacturer=data.get("Manufacturer"),
        model=data.get("Model"),
        badge=data.get("Badge"),
        year=int(year_raw) if year_raw is not None else None,
        mileage=int(mileage_raw) if mileage_raw is not None else None,
        price=int(price_raw) if price_raw is not None else None,
        fuel_type=data.get("FuelType"),
        region=data.get("OfficeCityState"),
        photo=data.get("Photo"),
        encar_url=f"https://fem.encar.com/cars/detail/{encar_id}",
        first_advertised_at=first_advertised_at,
        view_count=view_count,
    )
