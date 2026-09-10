"""
Chat Message Model
==================

SQLAlchemy 2.0 model representing a single chat message within a session.
Append-only log of patient and assistant interactions.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.session import SessionModel


class ChatMessageModel(Base, TimestampMixin):
    """
    Persistent representation of a chat message.
    """
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    session: Mapped["SessionModel"] = relationship(
        "SessionModel",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<ChatMessageModel id={self.id} chat_session_id={self.chat_session_id} role={self.role!r}>"
