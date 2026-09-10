"""
MEDHA Persistence Base & Declarative Models
===========================================

Defines the SQLAlchemy 2.0 DeclarativeBase and common model mixins.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _current_utc_timestamp() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in MEDHA.
    Enables unified metadata collection for Alembic autogenerate migrations.
    """
    pass


class TimestampMixin:
    """
    Reusable mixin providing timezone-aware created_at and updated_at timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_current_utc_timestamp,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_current_utc_timestamp,
        onupdate=_current_utc_timestamp,
        nullable=False,
    )
