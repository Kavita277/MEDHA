from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PatientBase(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    phone: str
    district: str
    case_id: str

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    district: Optional[str] = None
    case_id: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
