from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional

class VoiceCheckInResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    timepoint: str
    available: float
    message: str = "Voice check-in processed securely."

    model_config = ConfigDict(from_attributes=True)
