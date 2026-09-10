"""
Check-In Models
===============

SQLAlchemy 2.0 models for CheckIns and QuestionRecords.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any, Dict

from sqlalchemy import ForeignKey, String, Text, JSON, Uuid, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.persistence.models.session import SessionModel


class CheckInStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CheckInModel(Base, TimestampMixin):
    __tablename__ = "checkins"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    victim_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=CheckInStatus.PENDING.value)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_question_id: Mapped[Optional[str]] = mapped_column(String(64))

    session: Mapped["SessionModel"] = relationship("SessionModel")
    questions: Mapped[list["QuestionRecordModel"]] = relationship(
        "QuestionRecordModel",
        back_populates="checkin",
        order_by="QuestionRecordModel.question_order",
        cascade="all, delete-orphan",
    )


class QuestionRecordModel(Base, TimestampMixin):
    __tablename__ = "checkin_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    checkin_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("checkins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    answer: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    answer_status: Mapped[str] = mapped_column(String(32), default="pending")

    checkin: Mapped["CheckInModel"] = relationship("CheckInModel", back_populates="questions")
