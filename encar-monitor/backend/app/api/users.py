from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/me")
def get_current_user(
    telegram_id: int,
    db: Session = Depends(get_db),
):
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

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.get("")
def get_users(
    db: Session = Depends(get_db),
):
    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    return [
        {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]