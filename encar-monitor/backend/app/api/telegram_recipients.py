from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import TelegramRecipient
from app.auth import authenticated_user

import hmac


router = APIRouter(
    prefix="/api/telegram/recipients",
    tags=["Telegram"],
)


class TelegramRecipientCreate(BaseModel):
    telegram_id: int = Field(gt=0)


def verify_master_password(
    master_password: str | None,
) -> None:
    if not master_password or not hmac.compare_digest(
        master_password,
        settings.master_registration_password,
    ):
        raise HTTPException(
            status_code=403,
            detail="Неверный мастер-пароль",
        )


def require_management_access(
    master_password: str | None = Header(
        default=None,
        alias="X-Master-Password",
    ),
    _user=Depends(authenticated_user),
) -> None:
    verify_master_password(master_password)


@router.get("")
def get_recipients(
    _access=Depends(require_management_access),
    db: Session = Depends(get_db),
):
    recipients = db.scalars(
        select(TelegramRecipient)
        .order_by(TelegramRecipient.telegram_id)
    ).all()

    return [
        {
            "telegram_id": item.telegram_id,
            "created_at": item.created_at,
        }
        for item in recipients
    ]


@router.post("")
def add_recipient(
    data: TelegramRecipientCreate,
    _access=Depends(require_management_access),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(TelegramRecipient).where(
            TelegramRecipient.telegram_id == data.telegram_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Этот Telegram ID уже добавлен",
        )

    recipient = TelegramRecipient(
        telegram_id=data.telegram_id,
    )

    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    return {
        "telegram_id": recipient.telegram_id,
        "created_at": recipient.created_at,
    }


@router.delete("/{telegram_id}")
def delete_recipient(
    telegram_id: int,
    _access=Depends(require_management_access),
    db: Session = Depends(get_db),
):
    recipient = db.scalar(
        select(TelegramRecipient).where(
            TelegramRecipient.telegram_id == telegram_id
        )
    )

    if not recipient:
        raise HTTPException(
            status_code=404,
            detail="Telegram ID не найден",
        )

    db.delete(recipient)
    db.commit()

    return {
        "telegram_id": telegram_id,
        "deleted": True,
    }
