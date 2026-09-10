"""
Check-In API Schemas
====================

Strict boundaries to restrict internal ML predictions or model details
from leaking to the frontend.
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class QuestionResponse(BaseModel):
    id: uuid.UUID
    question_id: str
    question_text: str
    question_order: int
    answered_at: Optional[datetime] = None
    answer_status: str

    model_config = ConfigDict(from_attributes=True)


class CheckInResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_question_id: Optional[str] = None
    questions: List[QuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CheckInAnswerRequest(BaseModel):
    answer: Dict[str, Any]


class CheckInAnswerResponse(BaseModel):
    status: str
    checkin: CheckInResponse
    next_question: Optional[QuestionResponse] = None
