from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import MonitorSettings, User


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)

ALLOWED_INTERVALS = {1, 2, 5, 10, 30, 60}


class MonitorSettingsUpdate(BaseModel):
    enabled: bool | None = None
    interval_minutes: int | None = None


class MonitorSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    interval_minutes: int
    last_run_at: datetime | None
    next_run_at: datetime | None


def get_user(telegram_id: int, db: Session) -> User:
    user = db.scalar(
        select(User).where(User.telegram_id == telegram_id)
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


def get_or_create_settings(
    user: User,
    db: Session,
) -> MonitorSettings:
    monitor_settings = db.scalar(
        select(MonitorSettings).where(
            MonitorSettings.user_id == user.id
        )
    )

    if monitor_settings:
        return monitor_settings

    now = datetime.utcnow()

    monitor_settings = MonitorSettings(
        user_id=user.id,
        enabled=True,
        interval_minutes=settings.monitor_interval_minutes,
        next_run_at=now,
    )

    db.add(monitor_settings)
    db.commit()
    db.refresh(monitor_settings)

    return monitor_settings


@router.get(
    "/monitor",
    response_model=MonitorSettingsResponse,
)
def get_monitor_settings(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    user = get_user(telegram_id, db)

    return get_or_create_settings(user, db)


@router.patch(
    "/monitor",
    response_model=MonitorSettingsResponse,
)
def update_monitor_settings(
    data: MonitorSettingsUpdate,
    telegram_id: int,
    db: Session = Depends(get_db),
):
    user = get_user(telegram_id, db)
    monitor_settings = get_or_create_settings(user, db)

    if data.interval_minutes is not None:
        if data.interval_minutes not in ALLOWED_INTERVALS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Недопустимый интервал. "
                    "Доступно: 1, 2, 5, 10, 30, 60 минут."
                ),
            )

        monitor_settings.interval_minutes = data.interval_minutes

    if data.enabled is not None:
        monitor_settings.enabled = data.enabled

    # Apply the new settings immediately. The scheduler itself
    # runs every minute and executes only due users.
    if monitor_settings.enabled:
        monitor_settings.next_run_at = datetime.utcnow()
    else:
        monitor_settings.next_run_at = None

    db.commit()
    db.refresh(monitor_settings)

    return monitor_settings
