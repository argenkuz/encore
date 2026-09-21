from dataclasses import dataclass


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


def parse_car(data: dict) -> ParsedCar:
    encar_id = int(data["Id"])

    year_raw = data.get("Year")
    mileage_raw = data.get("Mileage")
    price_raw = data.get("Price")

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
    )