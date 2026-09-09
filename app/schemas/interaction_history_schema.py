from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InteractionHistoryBase(BaseModel):
    patient_id: str
    session_id: Optional[str] = None
    interaction_type: str
    summary: str

class InteractionHistoryCreate(InteractionHistoryBase):
    pass

class InteractionHistoryResponse(InteractionHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
