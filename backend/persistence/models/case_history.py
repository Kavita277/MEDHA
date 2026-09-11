"""
Case History Model
==================

SQLAlchemy 2.0 model representing a patient's longitudinal clinical intake background,
demographics, psychiatric/medical history, current medications, emergency contacts,
and treatment goals. Bound 1-to-1 to a Case.
"""

from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.case import Case
    from backend.persistence.models.user import User
    from backend.persistence.models.therapist import Therapist


class CaseHistoryModel(Base, TimestampMixin):
    """
    Comprehensive clinical intake and case history profile for an assigned patient case.
    """
    __tablename__ = "case_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
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

    # --- Demographics & Intake ---
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pronouns: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # --- Clinical Profile & Background ---
    primary_diagnosis: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    secondary_diagnosis: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    psychiatric_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medical_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    family_mental_health_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    substance_use_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trauma_or_stressors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_factors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    treatment_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(
        "Case",
        back_populates="case_history",
    )
    user: Mapped["User"] = relationship(
        "User",
    )
    therapist: Mapped["Therapist"] = relationship(
        "Therapist",
    )

    def __repr__(self) -> str:
        return f"<CaseHistoryModel id={self.id} case_id={self.case_id} primary_diagnosis={self.primary_diagnosis!r}>"
