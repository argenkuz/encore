from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models import User


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    master_password: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


def normalize_username(username: str) -> str:
    return username.strip().lower()


def validate_username(username: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    return bool(username) and all(char in allowed for char in username)


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if not verify_master_registration_password(data.master_password):
        raise HTTPException(
            status_code=403,
            detail="Неверный мастер-пароль",
        )

    username = normalize_username(data.username)

    if not validate_username(username):
        raise HTTPException(
            status_code=400,
            detail="Логин может содержать только латинские буквы, цифры, _ и -",
        )

    existing = db.scalar(select(User).where(User.username == username))
    if existing:
        raise HTTPException(status_code=409, detail="Такой логин уже существует")

    user = User(
        username=username,
        password_hash=hash_password(data.password),
        role="user",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
        },
    }


def verify_master_registration_password(value: str) -> bool:
    return __import__("hmac").compare_digest(
        value,
        settings.master_registration_password,
    )


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    username = normalize_username(data.username)
    user = db.scalar(select(User).where(User.username == username))

    if not user or not user.password_hash or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
        },
    }
