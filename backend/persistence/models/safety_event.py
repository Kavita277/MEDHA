import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Uuid
from backend.persistence.base import Base

class SafetyEventModel(Base):
    __tablename__ = "safety_events"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    status = Column(String, nullable=False, default="active")
    payload = Column(JSON, nullable=True)
    
    handled_at = Column(DateTime(timezone=True), nullable=True)
    handled_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
