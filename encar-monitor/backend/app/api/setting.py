from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)


ALLOWED_INTERVALS = {
    1,
    2,
    5,
    10,
    30,
    60,
}


class MonitorSettingsResponse(BaseModel):
    interval_minutes: int


class MonitorSettingsUpdate(BaseModel):
    interval_minutes: int


@router.get(
    "",
    response_model=MonitorSettingsResponse,
)
def get_settings():
    return {
        "interval_minutes": settings.monitor_interval_minutes,
    }


@router.patch(
    "",
    response_model=MonitorSettingsResponse,
)
def update_settings(
    data: MonitorSettingsUpdate,
):
    if data.interval_minutes not in ALLOWED_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Доступны интервалы: "
                "1, 2, 5, 10, 30, 60 минут."
            ),
        )

    settings.monitor_interval_minutes = (
        data.interval_minutes
    )

    return {
        "interval_minutes": (
            settings.monitor_interval_minutes
        ),
    }