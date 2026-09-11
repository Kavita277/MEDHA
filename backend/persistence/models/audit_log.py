"""
Audit Log Model
===============

SQLAlchemy 2.0 ORM model representing persistent compliance and security audit logs.

Design Contract:
  - Append-only compliance log recording sensitive security & clinical operations.
  - Strict Privacy Firewalls: NEVER stores passwords, JWT tokens, session secrets,
    raw audio, or full clinical transcripts.
  - Foreign key to users table with ON DELETE SET NULL to preserve audit trail
    if a user account is removed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base

if TYPE_CHECKING:
    from backend.persistence.models.user import User


class AuditLogModel(Base):
    """
    Persistent audit log record for compliance and security traceability.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Actor user (nullable for unauthenticated actions or deleted accounts)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actor_role: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="SUCCESS",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    actor: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<AuditLogModel id={self.id} actor={self.actor_user_id} "
            f"action={self.action!r} status={self.status!r} resource={self.resource_type}:{self.resource_id}>"
        )
