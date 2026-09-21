from aiogram import Bot, Dispatcher

from app.config import settings
from app.telegram.handlers import router


def create_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
    )

    dp = Dispatcher()

    dp.include_router(
        router,
    )

    return bot, dp