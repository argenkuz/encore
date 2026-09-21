from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Filter, User


router = APIRouter(
    prefix="/api/filters",
    tags=["Filters"],
)


class FilterCreate(BaseModel):
    telegram_id: int

    name: str

    manufacturer: str | None = None
    model_group: str | None = None
    model: str | None = None
    badge: str | None = None

    year_from: int | None = None
    month_from: int | None = None
    year_to: int | None = None
    month_to: int | None = None

    price_from: int | None = None
    price_to: int | None = None

    mileage_from: int | None = None
    mileage_to: int | None = None

    fuel_type: str | None = None
    transmission: str | None = None
    region: str | None = None


class FilterUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None

    manufacturer: str | None = None
    model_group: str | None = None
    model: str | None = None
    badge: str | None = None

    year_from: int | None = None
    month_from: int | None = None
    year_to: int | None = None
    month_to: int | None = None

    price_from: int | None = None
    price_to: int | None = None

    mileage_from: int | None = None
    mileage_to: int | None = None

    fuel_type: str | None = None
    transmission: str | None = None
    region: str | None = None


class FilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    enabled: bool

    manufacturer: str | None
    model_group: str | None
    model: str | None
    badge: str | None

    year_from: int | None
    month_from: int | None
    year_to: int | None
    month_to: int | None

    price_from: int | None
    price_to: int | None

    mileage_from: int | None
    mileage_to: int | None

    fuel_type: str | None
    transmission: str | None
    region: str | None


def get_user(
    telegram_id: int,
    db: Session,
) -> User:

    user = db.scalar(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=403,
            detail="User does not have access",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User is blocked",
        )

    return user


@router.get(
    "",
    response_model=list[FilterResponse],
)
def get_filters(
    telegram_id: int,
    db: Session = Depends(get_db),
):

    user = get_user(
        telegram_id,
        db,
    )

    filters = db.scalars(
        select(Filter)
        .where(Filter.user_id == user.id)
        .order_by(Filter.id)
    ).all()

    return filters


@router.get(
    "/{filter_id}",
    response_model=FilterResponse,
)
def get_filter(
    filter_id: int,
    telegram_id: int,
    db: Session = Depends(get_db),
):

    user = get_user(
        telegram_id,
        db,
    )

    filter_ = db.scalar(
        select(Filter).where(
            Filter.id == filter_id,
            Filter.user_id == user.id,
        )
    )

    if not filter_:
        raise HTTPException(
            status_code=404,
            detail="Filter not found",
        )

    return filter_


@router.post(
    "",
    response_model=FilterResponse,
)
def create_filter(
    data: FilterCreate,
    db: Session = Depends(get_db),
):

    user = get_user(
        data.telegram_id,
        db,
    )

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Filter name cannot be empty",
        )

    filter_ = Filter(
        user_id=user.id,
        name=data.name.strip(),

        manufacturer=data.manufacturer,
        model_group=data.model_group,
        model=data.model,
        badge=data.badge,

        year_from=data.year_from,
        month_from=data.month_from,
        year_to=data.year_to,
        month_to=data.month_to,

        price_from=data.price_from,
        price_to=data.price_to,

        mileage_from=data.mileage_from,
        mileage_to=data.mileage_to,

        fuel_type=data.fuel_type,
        transmission=data.transmission,
        region=data.region,
    )

    db.add(filter_)
    db.commit()
    db.refresh(filter_)

    return filter_


@router.patch(
    "/{filter_id}",
    response_model=FilterResponse,
)
def update_filter(
    filter_id: int,
    data: FilterUpdate,
    telegram_id: int,
    db: Session = Depends(get_db),
):

    user = get_user(
        telegram_id,
        db,
    )

    filter_ = db.scalar(
        select(Filter).where(
            Filter.id == filter_id,
            Filter.user_id == user.id,
        )
    )

    if not filter_:
        raise HTTPException(
            status_code=404,
            detail="Filter not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:
        if not update_data["name"].strip():
            raise HTTPException(
                status_code=400,
                detail="Filter name cannot be empty",
            )

        update_data["name"] = (
            update_data["name"].strip()
        )

    for field, value in update_data.items():
        setattr(
            filter_,
            field,
            value,
        )

    db.commit()
    db.refresh(filter_)

    return filter_


@router.delete(
    "/{filter_id}",
)
def delete_filter(
    filter_id: int,
    telegram_id: int,
    db: Session = Depends(get_db),
):

    user = get_user(
        telegram_id,
        db,
    )

    filter_ = db.scalar(
        select(Filter).where(
            Filter.id == filter_id,
            Filter.user_id == user.id,
        )
    )

    if not filter_:
        raise HTTPException(
            status_code=404,
            detail="Filter not found",
        )

    db.delete(filter_)
    db.commit()

    return {
        "status": "deleted",
        "filter_id": filter_id,
    }