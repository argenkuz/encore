from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import authenticated_user
from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/me")
def get_current_user(
    user: User = Depends(authenticated_user),
):
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.get("")
def get_users(
    user: User = Depends(authenticated_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    return [
        {
            "id": item.id,
            "telegram_id": item.telegram_id,
            "username": item.username,
            "role": item.role,
            "is_active": item.is_active,
            "created_at": item.created_at,
        }
        for item in users
    ]
