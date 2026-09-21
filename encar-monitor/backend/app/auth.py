import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User


def validate_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram authorization is required")

    try:
        values = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = values.pop("hash", None)
        auth_date = int(values.get("auth_date", "0"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid Telegram init data")

    if not received_hash:
        raise HTTPException(status_code=401, detail="Invalid Telegram init data")

    if time.time() - auth_date > settings.telegram_auth_max_age_seconds:
        raise HTTPException(status_code=401, detail="Telegram authorization expired")

    data_check_string = "\\n".join(
        f"{key}={value}"
        for key, value in sorted(values.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    user_raw = values.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Telegram user is missing")

    try:
        user_data = json.loads(user_raw)
        telegram_id = int(user_data["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid Telegram user data")

    return {
        "telegram_id": telegram_id,
        "username": user_data.get("username"),
        "first_name": user_data.get("first_name"),
        "last_name": user_data.get("last_name"),
    }


def get_current_user(
    db: Session,
    init_data: str | None,
    dev_telegram_id: str | None = None,
) -> User:
    if settings.environment == "development" and dev_telegram_id:
        try:
            telegram_id = int(dev_telegram_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid development user")

        user = db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if not user:
            raise HTTPException(status_code=403, detail="User does not have access")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is blocked")
        return user

    data = validate_init_data(init_data or "")
    user = db.scalar(
        select(User).where(User.telegram_id == data["telegram_id"])
    )

    if not user:
        raise HTTPException(status_code=403, detail="User does not have access")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is blocked")

    if user.username != data["username"]:
        user.username = data["username"]
        db.commit()
        db.refresh(user)

    return user


from app.database import get_db


def authenticated_user(
    db: Session = Depends(get_db),
    init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    dev_telegram_id: str | None = Header(default=None, alias="X-Dev-Telegram-Id"),
) -> User:
    return get_current_user(
        db=db,
        init_data=init_data,
        dev_telegram_id=dev_telegram_id,
    )
