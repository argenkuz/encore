from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import User


router = Router()


def get_or_create_user(message: Message) -> User | None:
    """
    Создаёт пользователя только если его Telegram ID
    совпадает с ADMIN_TELEGRAM_ID.

    Обычные пользователи пока должны быть добавлены
    администратором вручную.
    """

    telegram_user = message.from_user

    if telegram_user is None:
        return None

    telegram_id = telegram_user.id

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user:
            return user

        # Первый администратор
        if telegram_id == settings.admin_telegram_id:

            user = User(
                telegram_id=telegram_id,
                username=telegram_user.username,
                role="admin",
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            return user

        return None

    finally:
        db.close()


@router.message(CommandStart())
async def start_handler(message: Message):

    user = get_or_create_user(message)

    if user is None:
        await message.answer(
            "⛔ У Вас нет доступа к этому боту."
        )
        return

    if not user.is_active:
        await message.answer(
            "⛔ Ваш аккаунт заблокирован."
        )
        return

    if user.role == "admin":

        await message.answer(
            "👋 Добро пожаловать, администратор!\n\n"
            "🚗 Encar Monitor готов к работе."
        )

    else:

        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "🚗 Encar Monitor готов к работе."
        )