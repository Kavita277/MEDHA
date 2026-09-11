"""
Clinical Event Model
====================

SQLAlchemy 2.0 model representing discrete clinical timeline milestones,
such as session notes, medication adjustments, crisis episodes, panic attacks,
life stressors, hospital visits, or therapeutic breakthroughs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.case import Case
    from backend.persistence.models.user import User
    from backend.persistence.models.therapist import Therapist


class ClinicalEventModel(Base, TimestampMixin):
    """
    Chronological clinical event or milestone logged by a clinician for an assigned case.
    """
    __tablename__ = "case_clinical_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    therapist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("therapists.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Descriptive summary / title
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Standard clinical category
    # (e.g. SESSION_NOTE, MEDICATION_CHANGE, PANIC_ATTACK, CRISIS_INCIDENT, LIFE_STRESSOR, HOSPITAL_VISIT, MILESTONE, OTHER)
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="SESSION_NOTE",
        index=True,
    )

    # Clinical severity rating: LOW, MEDIUM, HIGH, CRITICAL
    severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="MEDIUM",
        index=True,
    )

    # When the event occurred in the patient's real life
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Detailed clinical observations, triggers, narrative
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Clinical action taken, prescription advice, intervention
    action_taken: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Optional structured payload for future metadata
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    case: Mapped["Case"] = relationship(
        "Case",
        back_populates="clinical_events",
    )
    user: Mapped["User"] = relationship(
        "User",
    )
    therapist: Mapped["Therapist"] = relationship(
        "Therapist",
    )

    def __repr__(self) -> str:
        return f"<ClinicalEventModel id={self.id} case_id={self.case_id} type={self.event_type} title={self.title!r}>"
