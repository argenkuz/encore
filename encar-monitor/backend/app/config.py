from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "sqlite:///./encar.db"
    admin_telegram_id: int
    monitor_interval_minutes: int = 5
    log_level: str = "INFO"
    frontend_url: str | None = None
    environment: str = "production"
    telegram_auth_max_age_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()