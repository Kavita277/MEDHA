from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import List

class JournalEntryCreate(BaseModel):
    content: str

class JournalEntryUpdate(BaseModel):
    content: str

class JournalEntryResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JournalEntryListResponse(BaseModel):
    entries: List[JournalEntryResponse]
