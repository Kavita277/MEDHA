from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RiskHistory(Base):
    __tablename__ = "risk_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    text_score = Column(Float)
    voice_score = Column(Float)
    behaviour_score = Column(Float)
    structured_score = Column(Float)
    temporal_score = Column(Float)
    
    dds = Column(Float)
    risk_level = Column(String)
    confidence = Column(Float)
    recommendation = Column(JSON) # Can be list of strings
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("Patient", backref="risk_histories")

class InteractionHistory(Base):
    __tablename__ = "interaction_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), index=True)
    session_id = Column(String, index=True, nullable=True)
    interaction_type = Column(String) # Text / Voice / Chatbot / IVRS / Web Portal
    summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("Patient", backref="interaction_histories")
