from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SeenCar


def is_new_car(
    db: Session,
    filter_id: int,
    encar_id: int,
) -> bool:

    existing = db.scalar(
        select(SeenCar).where(
            SeenCar.filter_id == filter_id,
            SeenCar.encar_id == encar_id,
        )
    )

    return existing is None


def mark_car_as_seen(
    db: Session,
    filter_id: int,
    encar_id: int,
) -> None:

    seen_car = SeenCar(
        filter_id=filter_id,
        encar_id=encar_id,
    )

    db.add(seen_car)
    db.commit()