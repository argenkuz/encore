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

    # Lightweight compatibility migrations for existing SQLite databases.
    # SQLite cannot change a column's NULL constraint with ALTER COLUMN, so
    # rebuild the legacy users table when telegram_id is still NOT NULL.
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

        telegram_column = next(
            column
            for column in inspector.get_columns("users")
            if column["name"] == "telegram_id"
        )

        if telegram_column["nullable"] is False:
            with engine.begin() as connection:
                connection.execute(text("PRAGMA foreign_keys=OFF"))
                connection.execute(text("DROP TABLE IF EXISTS users_new"))
                connection.execute(text("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY,
                        telegram_id INTEGER,
                        username VARCHAR(255),
                        password_hash VARCHAR(512),
                        role VARCHAR(50) NOT NULL,
                        is_active BOOLEAN NOT NULL,
                        created_at DATETIME NOT NULL
                    )
                """))
                connection.execute(text("""
                    INSERT INTO users_new
                        (id, telegram_id, username, password_hash, role, is_active, created_at)
                    SELECT
                        id, telegram_id, username, password_hash, role, is_active, created_at
                    FROM users
                """))
                connection.execute(text("DROP TABLE users"))
                connection.execute(text("ALTER TABLE users_new RENAME TO users"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_id ON users (telegram_id)"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
                connection.execute(text("PRAGMA foreign_keys=ON"))

    # PostgreSQL stores SQLAlchemy Integer as INT4. Telegram IDs can exceed
    # the INT4 limit, so widen Telegram ID columns to BIGINT on existing DBs.
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE users
                ALTER COLUMN telegram_id TYPE BIGINT
            """))
            connection.execute(text("""
                ALTER TABLE telegram_recipients
                ALTER COLUMN telegram_id TYPE BIGINT
            """))

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
