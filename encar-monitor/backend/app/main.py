from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot

from app.config import settings
from app.database import init_db

from app.api.filters import router as filters_router
from app.api.users import router as users_router
from app.api.catalog import router as catalog_router
from app.api.settings import router as settings_router

from app.telegram.bot import create_bot
from app.monitoring.scheduler import MonitorScheduler


# =========================================================
# GLOBAL OBJECTS
# =========================================================

bot: Bot | None = None
monitor_scheduler: MonitorScheduler | None = None


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot
    global monitor_scheduler

    print("Starting Encar Monitor...")

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    init_db()

    print("Database initialized.")


    # -----------------------------------------------------
    # TELEGRAM BOT
    # -----------------------------------------------------

    bot, _ = create_bot()

    print("Telegram bot created.")


    # -----------------------------------------------------
    # MONITOR SCHEDULER
    # -----------------------------------------------------

    monitor_scheduler = MonitorScheduler(
        bot=bot,
    )

    monitor_scheduler.start()

    print(
        f"Monitor started "
        f"({settings.monitor_interval_minutes} min)."
    )


    # -----------------------------------------------------
    # APPLICATION STARTED
    # -----------------------------------------------------

    print("Encar Monitor started successfully.")

    try:
        yield

    finally:
        print("Stopping Encar Monitor...")

        # -------------------------------------------------
        # STOP SCHEDULER
        # -------------------------------------------------

        if monitor_scheduler is not None:
            await monitor_scheduler.stop()

        # -------------------------------------------------
        # STOP TELEGRAM BOT
        # -------------------------------------------------

        if bot is not None:
            await bot.session.close()

        print("Encar Monitor stopped.")


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Encar Monitor",
    description="Encar vehicle monitoring service",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *([settings.frontend_url] if settings.frontend_url else []),
    ],

    # Allows Railway preview/production domains when FRONTEND_URL is not set.
    allow_origin_regex=r"https://.*\\.up\\.railway\\.app",

    allow_credentials=True,

    allow_methods=[
        "*",
    ],

    allow_headers=[
        "*",
    ],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    filters_router,
)

app.include_router(
    users_router,
)

app.include_router(
    catalog_router,
)

app.include_router(
    settings_router,
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
async def root():
    return {
        "service": "Encar Monitor",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }