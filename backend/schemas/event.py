"""
Event Schemas
=============
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    event_id: str
    case_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    event_type: str = Field(..., max_length=100)
    occurred_at: datetime
    metadata_payload: Optional[Dict[str, Any]] = None


class EventBatchRequest(BaseModel):
    events: List[EventCreate]


class EventBatchResponse(BaseModel):
    status: str
    received_count: int
    processed_count: int
    ignored_duplicate_count: int
