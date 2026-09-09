from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    district = Column(String)
    case_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
