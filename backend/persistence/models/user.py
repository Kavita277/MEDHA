"""
User Model & Enumerations
=========================

SQLAlchemy 2.0 model for user identity, authentication, and lifecycle tracking.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.therapist import Therapist
    from backend.persistence.models.case import Case


class UserRole(str, enum.Enum):
    """User authorization roles."""
    USER = "USER"
    THERAPIST = "THERAPIST"


class UserStatus(str, enum.Enum):
    """Account operational states."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class User(Base, TimestampMixin):
    """
    Core account and authentication record for all human actors.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=32),
        nullable=False,
        default=UserRole.USER,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mobile: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        unique=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=False, length=32),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True,
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 1-to-1 relationship with Therapist profile
    therapist: Mapped[Optional["Therapist"]] = relationship(
        "Therapist",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-N relationship with longitudinal cases
    cases: Mapped[list["Case"]] = relationship(
        "Case",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value!r} status={self.status.value!r}>"
