from __future__ import annotations


# Encar separates Korean/domestic manufacturers (Y) from imported
# manufacturers (N). Keep the mapping by manufacturer name so the
# monitor can build the correct search query automatically.
DOMESTIC_MANUFACTURERS = {
    "현대",
    "제네시스",
    "기아",
    "쉐보레(GM대우)",
    "쉐보레",
    "르노코리아(삼성)",
    "르노코리아",
    "KG모빌리티(쌍용)",
    "KG모빌리티",
    "기타 제조사",
}


def get_car_type(manufacturer: str | None) -> str:
    """Return Encar CarType for a manufacturer: Y=domestic, N=imported."""
    if not manufacturer:
        return "Y"

    normalized = " ".join(manufacturer.strip().split())

    if normalized in DOMESTIC_MANUFACTURERS:
        return "Y"

    return "N"
