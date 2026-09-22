import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User


def _secret() -> bytes:
    return (settings.auth_secret or settings.bot_token).encode()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    salt_part = base64.urlsafe_b64encode(salt).decode()
    hash_part = base64.urlsafe_b64encode(derived).decode()
    return "scrypt$" + salt_part + "$" + hash_part


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_raw, hash_raw = stored.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_raw.encode())
        expected = base64.urlsafe_b64decode(hash_raw.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + 60 * 60 * 24 * 30}
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    signature = hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def get_user_from_token(token: str, db: Session) -> User:
    try:
        raw, signature = token.split(".", 1)
        expected = hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid access token")

        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))

        if int(payload["exp"]) < int(time.time()):
            raise HTTPException(status_code=401, detail="Access token expired")

        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is blocked")
    return user


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

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(values.items())
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
    access_token: str | None = None,
) -> User:
    if access_token:
        return get_user_from_token(access_token, db)

    if settings.environment == "development" and dev_telegram_id:
        try:
            telegram_id = int(dev_telegram_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid development user")

        user = db.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            raise HTTPException(status_code=403, detail="User does not have access")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is blocked")
        return user

    if init_data:
        data = validate_init_data(init_data)
        user = db.scalar(select(User).where(User.telegram_id == data["telegram_id"]))
        if not user:
            raise HTTPException(status_code=403, detail="User does not have access")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is blocked")
        return user

    raise HTTPException(status_code=401, detail="Authentication required")


def authenticated_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    dev_telegram_id: str | None = Header(default=None, alias="X-Dev-Telegram-Id"),
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    return get_current_user(
        db=db,
        init_data=init_data,
        dev_telegram_id=dev_telegram_id,
        access_token=token,
    )
