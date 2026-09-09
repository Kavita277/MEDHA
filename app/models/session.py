from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    
    answers = relationship("Answer", back_populates="session")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.session_id"))
    question_id = Column(String)
    answer_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="answers")
