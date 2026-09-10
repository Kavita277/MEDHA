"""
Session Model
=============

SQLAlchemy 2.0 model representing a chat conversation session within a case.
Stores active session status, timepoint, and persistent MedhaState snapshots.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.case import Case
    from backend.persistence.models.chat_message import ChatMessageModel


class SessionStatus(str, enum.Enum):
    """Authoritative lifecycle states for MEDHA conversation sessions."""
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    EXPIRED = "EXPIRED"


class SessionModel(Base, TimestampMixin):
    """
    Persistent representation of a conversation session linked to a case.
    Stores the full MedhaState snapshot for seamless state restoration across turns.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    session_identifier: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    timepoint: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SessionStatus.ACTIVE.value,
        index=True,
    )
    state_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    case: Mapped["Case"] = relationship(
        "Case",
        back_populates="sessions",
    )
    messages: Mapped[list["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        order_by="ChatMessageModel.created_at",
    )

    def __repr__(self) -> str:
        return f"<SessionModel id={self.id} session_identifier={self.session_identifier!r} case_id={self.case_id} status={self.status}>"
