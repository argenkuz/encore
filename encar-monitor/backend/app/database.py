from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight compatibility migration for existing SQLite databases.
    # New installations get the column from SQLAlchemy metadata.
    inspector = inspect(engine)

    if "users" in inspector.get_table_names():
        columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }

        if "password_hash" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(512)")
                )

    # Optional production bootstrap for the first administrator.
    if settings.admin_username and settings.admin_password:
        from app.auth import hash_password

        db = SessionLocal()
        try:
            admin = db.query(models.User).filter(
                models.User.telegram_id == settings.admin_telegram_id
            ).first()

            if admin is None:
                admin = models.User(
                    telegram_id=settings.admin_telegram_id,
                    username=settings.admin_username.strip().lower(),
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                    is_active=True,
                )
                db.add(admin)
            else:
                admin.username = settings.admin_username.strip().lower()
                admin.password_hash = hash_password(settings.admin_password)
                admin.role = "admin"
                admin.is_active = True

            db.commit()
        finally:
            db.close()
