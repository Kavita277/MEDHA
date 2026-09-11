"""
Prediction Result Model
=======================

SQLAlchemy 2.0 ORM model persisting MEDHA V2 prediction outputs per Case / Session.

Design Principles:
- All specialist predictions (struct, text, voice, behav) are nullable.
  MISSING != ZERO. A null field means the result is genuinely unavailable.
- The Behaviour Specialist (behav_pred) is currently blocked (Step 10).
  behav_pred stays null until the PredictionService populates it.
- Future PredictionService integration: populate this table via the
  PredictionResultRepository; the API layer reads from it without modification.
- Triage is persisted for auditability; it can also be computed at read-time
  via TriageService when the stored value is absent.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.case import Case
    from backend.persistence.models.session import SessionModel


class PredictionResultModel(Base, TimestampMixin):
    """
    Persistent MEDHA V2 prediction record for a Case at a given timepoint.

    May be linked to a specific session (session_id) or be case-level (session_id = NULL).
    All specialist predictions are nullable; null means genuinely unavailable.
    """

    __tablename__ = "prediction_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership chain: prediction → case → therapist
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nullable: result may be case-level (not tied to a specific session)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    timepoint: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Unified Prediction Outputs (Single Source of Truth)
    # ------------------------------------------------------------------
    # Canonical columns (nullable; missing != zero, NULL not NaN)
    structured_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    text_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voice_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    behaviour_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fusion_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temporal_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    future_escalation_flag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    triage_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Backward-compatible SQLAlchemy synonyms
    struct_pred = synonym("structured_score")
    text_pred = synonym("text_score")
    voice_pred = synonym("voice_score")
    behav_pred = synonym("behaviour_score")
    fusion_dds_prediction = synonym("fusion_score")
    temporal_risk_score = synonym("temporal_risk")

    # ------------------------------------------------------------------
    # Modality Availability Flags (persisted for auditability)
    # ------------------------------------------------------------------
    struct_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    text_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    behav_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # When the prediction was generated (not when persisted)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    case: Mapped["Case"] = relationship("Case")
    session: Mapped[Optional["SessionModel"]] = relationship("SessionModel")

    def __repr__(self) -> str:
        return (
            f"<PredictionResultModel id={self.id} case_id={self.case_id} "
            f"timepoint={self.timepoint} triage={self.triage_level!r}>"
        )
