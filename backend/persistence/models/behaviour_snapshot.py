"""
Behaviour Feature Snapshot Model
================================
Persists the 10 authoritative behaviour features for a Case at a specific Timepoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base

if TYPE_CHECKING:
    from backend.persistence.models.case import Case

class BehaviourFeatureSnapshotModel(Base):
    __tablename__ = "behaviour_feature_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    timepoint: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 10 Authoritative Features
    app_interaction_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    app_interaction_duration_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checkin_response_delay: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checkin_response_delay_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checkin_completion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    missed_checkin_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    journal_entry_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chat_message_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    late_night_usage_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    support_resource_access_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    aggregated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    case: Mapped["Case"] = relationship("Case")

    __table_args__ = (
        UniqueConstraint("case_id", "timepoint", name="uix_case_timepoint_behaviour"),
    )
