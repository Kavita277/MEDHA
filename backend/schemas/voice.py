from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

class VoiceCheckInResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    timepoint: str
    available: float
    audio_filename: Optional[str] = None
    duration_seconds: Optional[float] = None
    voice_score: Optional[float] = None
    transcript: Optional[str] = None
    processed_at: Optional[datetime] = None
    message: str = "Voice check-in processed securely."

    model_config = ConfigDict(from_attributes=True)

class VoiceRecordReviewResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    timepoint: str
    audio_filename: Optional[str] = None
    duration_seconds: Optional[float] = None
    extracted_features: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    voice_score: Optional[float] = None
    processed_at: Optional[datetime] = None
    available: float

    model_config = ConfigDict(from_attributes=True)
