from contextlib import asynccontextmanager, suppress
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot

from app.config import settings
from sqlalchemy import func, select

from app.database import SessionLocal, init_db
from app.models import CatalogManufacturer
from app.encar.import_catalog import import_catalog

from app.api.auth import router as auth_router
from app.api.filters import router as filters_router
from app.api.users import router as users_router
from app.api.catalog import router as catalog_router
from app.api.settings import router as settings_router
from app.api.telegram_recipients import router as telegram_recipients_router

from app.telegram.bot import create_bot
from app.monitoring.scheduler import MonitorScheduler


# =========================================================
# GLOBAL OBJECTS
# =========================================================

bot: Bot | None = None
monitor_scheduler: MonitorScheduler | None = None
telegram_polling_task: asyncio.Task | None = None
catalog_bootstrap_task: asyncio.Task | None = None


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot
    global monitor_scheduler
    global telegram_polling_task
    global catalog_bootstrap_task

    print("Starting Encar Monitor...")

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    init_db()

    print("Database initialized.")

    # -----------------------------------------------------
    # CATALOG BOOTSTRAP
    # -----------------------------------------------------

    async def bootstrap_catalog():
        db = SessionLocal()
        try:
            manufacturers_count = db.scalar(
                select(func.count()).select_from(CatalogManufacturer)
            )
        finally:
            db.close()

        if manufacturers_count:
            print(
                f"Catalog already initialized ({manufacturers_count} manufacturers)."
            )
            return

        print("Catalog is empty. Starting Encar catalog import...")

        try:
            await import_catalog()
            print("Encar catalog import completed.")
        except Exception as error:
            print(f"Encar catalog import failed: {error}")

    catalog_bootstrap_task = asyncio.create_task(bootstrap_catalog())


    # -----------------------------------------------------
    # TELEGRAM BOT
    # -----------------------------------------------------

    bot, dispatcher = create_bot()

    print("Telegram bot created.")

    # Start Telegram long polling in the background.
    # FastAPI and the Telegram bot can run in the same process.
    telegram_polling_task = asyncio.create_task(
        dispatcher.start_polling(bot),
    )

    print("Telegram polling started.")


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
        # STOP CATALOG BOOTSTRAP
        # -------------------------------------------------

        if catalog_bootstrap_task is not None:
            catalog_bootstrap_task.cancel()
            with suppress(asyncio.CancelledError):
                await catalog_bootstrap_task

        # -------------------------------------------------
        # STOP TELEGRAM POLLING
        # -------------------------------------------------

        if telegram_polling_task is not None:
            telegram_polling_task.cancel()
            with suppress(asyncio.CancelledError):
                await telegram_polling_task

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
        "http://10.206.36.233:5173",
        *([settings.frontend_url] if settings.frontend_url else []),
    ],

    # Allows Railway preview/production domains when FRONTEND_URL is not set.
    allow_origin_regex=r"(https?://[^/]+:5173|https://.*\.ngrok(-free)?\.app)",

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
    auth_router,
)

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

app.include_router(
    telegram_recipients_router,
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