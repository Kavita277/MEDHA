from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RiskHistoryBase(BaseModel):
    patient_id: str
    text_score: Optional[float] = None
    voice_score: Optional[float] = None
    behaviour_score: Optional[float] = None
    structured_score: Optional[float] = None
    temporal_score: Optional[float] = None
    dds: float
    risk_level: str
    confidence: float
    recommendation: Optional[List[str]] = None
    processing_time_ms: float

class RiskHistoryCreate(RiskHistoryBase):
    pass

class RiskHistoryResponse(RiskHistoryBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class RiskHistoryChronological(BaseModel):
    date: str
    dds: float
    risk: str
