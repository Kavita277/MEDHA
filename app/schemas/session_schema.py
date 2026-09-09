from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class SessionCreate(BaseModel):
    session_id: str
    patient_id: str

class AnswerCreate(BaseModel):
    question_id: str
    answer_data: Dict[str, Any]

class AnswerResponse(BaseModel):
    id: int
    question_id: str
    answer_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    session_id: str
    patient_id: str
    status: str
    created_at: datetime
    answers: List[AnswerResponse] = []

    class Config:
        from_attributes = True
