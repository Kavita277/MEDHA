"""
Therapist Model
===============

SQLAlchemy 2.0 model representing clinician profile data bound to an authenticated user.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.user import User
    from backend.persistence.models.case import Case


class Therapist(Base, TimestampMixin):
    """
    Specialized profile metadata for authenticated users with THERAPIST role.
    """
    __tablename__ = "therapists"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # 1-to-1 relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="therapist",
    )

    # 1-to-N relationship with assigned Cases
    cases: Mapped[list["Case"]] = relationship(
        "Case",
        back_populates="therapist",
    )

    def __repr__(self) -> str:
        return f"<Therapist id={self.id} user_id={self.user_id} display_name={self.display_name!r}>"
