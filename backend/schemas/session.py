"""
Session Pydantic Schemas
========================

Schemas for session creation, reading, and status updates.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.persistence.models.session import SessionStatus


class SessionCreateRequest(BaseModel):
    """Payload for initializing a new chat conversation session."""
    case_id: Optional[uuid.UUID] = Field(
        None,
        description="Target case ID. Optional for patient (defaults to active case); required for therapist.",
    )
    session_identifier: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional custom string identifier for session. Auto-generated if omitted.",
    )


class SessionResponse(BaseModel):
    """Serialized representation of a conversation session."""
    id: uuid.UUID
    case_id: uuid.UUID
    victim_id: str
    session_identifier: str
    timepoint: int
    status: str
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    state_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SessionStatusUpdate(BaseModel):
    """Payload for updating session lifecycle status."""
    status: SessionStatus
