"""
MEDHA ORM Models Package
========================

Contains SQLAlchemy declarative ORM models.
Exports all registered domain entities so they attach to Base.metadata.
"""

from backend.persistence.base import Base, TimestampMixin
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel
from backend.persistence.models.event import RawEventModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.audit_log import AuditLogModel

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "UserStatus",
    "Therapist",
    "Case",
    "SessionModel",
    "SessionStatus",
    "ChatMessageModel",
    "CheckInModel",
    "QuestionRecordModel",
    "RawEventModel",
    "BehaviourFeatureSnapshotModel",
    "PredictionResultModel",
    "VoiceRecordModel",
    "JournalEntryModel",
    "SafetyEventModel",
    "AuditLogModel",
]

