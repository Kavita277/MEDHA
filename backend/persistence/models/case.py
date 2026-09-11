"""
Case Model
==========

SQLAlchemy 2.0 model representing a longitudinal case container
linking a patient (User) to an assigned clinician (Therapist) and Victim_ID.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.user import User
    from backend.persistence.models.therapist import Therapist
    from backend.persistence.models.session import SessionModel
    from backend.persistence.models.voice_record import VoiceRecordModel
    from backend.persistence.models.journal_entry import JournalEntryModel
    from backend.persistence.models.case_history import CaseHistoryModel
    from backend.persistence.models.clinical_event import ClinicalEventModel


class Case(Base, TimestampMixin):
    """
    Longitudinal container connecting a patient to an assigned therapist.
    Maintains Victim_ID for compatibility with the frozen MEDHA V2 pipeline.
    """
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    victim_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    therapist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("therapists.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    current_timepoint: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        index=True,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="cases",
    )
    therapist: Mapped["Therapist"] = relationship(
        "Therapist",
        back_populates="cases",
    )
    sessions: Mapped[List["SessionModel"]] = relationship(
        "SessionModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    voice_records: Mapped[List["VoiceRecordModel"]] = relationship(
        "VoiceRecordModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    journal_entries: Mapped[List["JournalEntryModel"]] = relationship(
        "JournalEntryModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    case_history: Mapped[Optional["CaseHistoryModel"]] = relationship(
        "CaseHistoryModel",
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan",
    )
    clinical_events: Mapped[List["ClinicalEventModel"]] = relationship(
        "ClinicalEventModel",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="desc(ClinicalEventModel.occurred_at)",
    )

    def __repr__(self) -> str:
        return f"<Case id={self.id} victim_id={self.victim_id!r} user_id={self.user_id} therapist_id={self.therapist_id}>"

