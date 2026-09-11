import uuid
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.persistence.base import Base, TimestampMixin

class VoiceRecordModel(Base, TimestampMixin):
    __tablename__ = "voice_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    timepoint = Column(String, nullable=False, index=True)
    audio_filename = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    extracted_features = Column(JSON, nullable=True)
    transcript = Column(Text, nullable=True)
    voice_score = Column(Float, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    available = Column(Float, nullable=False, default=0.0)

    # Relationships
    case = relationship("Case", back_populates="voice_records")
    session = relationship("SessionModel")
