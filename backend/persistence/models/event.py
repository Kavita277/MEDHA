"""
Event Model
===========

Persistence model for raw behavioral event ingestion.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base

if TYPE_CHECKING:
    from backend.persistence.models.case import Case
    from backend.persistence.models.session import SessionModel


class RawEventModel(Base):
    """
    Append-only raw behavioral events.
    """
    __tablename__ = "raw_events"

    # Surrogate PK
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Client-generated Event ID (Unique) used for idempotency
    event_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case")
    session: Mapped[Optional["SessionModel"]] = relationship("SessionModel")
