from pydantic import BaseModel
from typing import List, Dict, Any, Union
from app.schemas.patient_schema import PatientResponse

class TimelineEvent(BaseModel):
    type: str
    timestamp: str
    data: Dict[str, Any]

class TimelineResponse(BaseModel):
    patient: PatientResponse
    events: List[TimelineEvent]
