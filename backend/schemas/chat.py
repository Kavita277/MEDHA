"""
Chat Schemas
============

Pydantic schemas for chat requests and responses.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Payload for sending a new message to the chatbot."""
    message: str = Field(..., min_length=1, description="The user's message content")
    language: Optional[str] = Field(None, description="Optional language hint (e.g., 'en', 'hi', 'hinglish')")
    behaviour_data: Optional[Dict[str, Any]] = Field(None, description="Optional behavioural telemetry")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional per-turn metadata")


class ChatMessageResponse(BaseModel):
    """
    Sanitized representation of a single chat message.
    Never exposes internal risk scores or prediction details to the user.
    """
    id: uuid.UUID
    chat_session_id: uuid.UUID
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatTurnResult(BaseModel):
    """
    Response returned to the user after processing a message.
    Contains the new assistant message and updated session metadata,
    but absolutely no predictive scores or internal ML state.
    """
    session_id: str
    turn_index: int
    user_message: str
    assistant_response: str
    timestamp: datetime
    safety_triggered: bool = False


class ChatHistoryResponse(BaseModel):
    """Payload containing ordered messages for a session."""
    session_id: uuid.UUID
    messages: List[ChatMessageResponse]

    class Config:
        from_attributes = True
