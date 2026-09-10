"""
Chat API Endpoints
==================

Routes for sending messages to the MEDHA chatbot and retrieving chat history.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.user import User
from backend.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageCreate,
    ChatTurnResult,
)
from backend.security.dependencies import get_current_user
from backend.services.chatbot_service import ChatbotService

router = APIRouter()


@router.post("/sessions/{session_id}/message", response_model=ChatTurnResult)
def process_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatTurnResult:
    """
    Processes a chat message through the MEDHA pipeline.
    Appends the user message and assistant response to the session history.
    """
    chat_service = ChatbotService(db)
    return chat_service.process_message(
        session_id=session_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Retrieves the chronologically ordered chat history for an active session.
    Enforces RBAC data boundaries.
    """
    chat_service = ChatbotService(db)
    return chat_service.get_chat_history(
        session_id=session_id,
        current_user=current_user,
    )
