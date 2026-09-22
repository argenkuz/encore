from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    filters = relationship(
        "Filter",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Filter(Base):
    __tablename__ = "filters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ---------------------------------------------------------
    # ENCAR
    # ---------------------------------------------------------

    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model_group: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    badge: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ---------------------------------------------------------
    # YEAR / MONTH
    # ---------------------------------------------------------

    year_from: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    month_from: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    year_to: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    month_to: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ---------------------------------------------------------
    # PRICE
    # ---------------------------------------------------------

    price_from: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    price_to: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ---------------------------------------------------------
    # MILEAGE
    # ---------------------------------------------------------

    mileage_from: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    mileage_to: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ---------------------------------------------------------
    # OTHER
    # ---------------------------------------------------------

    fuel_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    transmission: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="filters",
    )


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    encar_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    badge: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    fuel_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    photo: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    encar_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class SeenCar(Base):
    """
    Связь:
        какой фильтр
        какую машину
        уже видел
    """

    __tablename__ = "seen_cars"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    filter_id: Mapped[int] = mapped_column(
        ForeignKey("filters.id"),
        nullable=False,
    )

    encar_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "filter_id",
            "encar_id",
            name="uq_filter_car",
        ),
    )


class CatalogManufacturer(Base):
    __tablename__ = "catalog_manufacturers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    models: Mapped[list["CatalogModel"]] = relationship(
        "CatalogModel",
        back_populates="manufacturer",
        cascade="all, delete-orphan",
    )


class CatalogModel(Base):
    __tablename__ = "catalog_models"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_manufacturers.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    manufacturer: Mapped["CatalogManufacturer"] = relationship(
        "CatalogManufacturer",
        back_populates="models",
    )

    badges: Mapped[list["CatalogBadge"]] = relationship(
        "CatalogBadge",
        back_populates="model",
        cascade="all, delete-orphan",
    )


class CatalogBadge(Base):
    __tablename__ = "catalog_badges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_models.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    model: Mapped["CatalogModel"] = relationship(
        "CatalogModel",
        back_populates="badges",
    )

class MonitorSettings(Base):
    __tablename__ = "monitor_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
    )


class TelegramRecipient(Base):
    __tablename__ = "telegram_recipients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
