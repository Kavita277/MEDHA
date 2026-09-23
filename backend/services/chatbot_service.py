"""
Chatbot Orchestration Service
=============================

Coordinates incoming chat requests, MedhaState restoration, 
the ConversationManager, and message persistence.
"""

from __future__ import annotations

import logging
import uuid
from typing import Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.integrations.session_state_adapter import (
    attach_to_conversation_manager,
    sync_from_conversation_manager,
)
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.session import SessionStatus
from backend.persistence.models.user import User
from backend.persistence.repositories.chat_message import ChatMessageRepository
from backend.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatTurnResult,
)
from backend.config import get_settings
from backend.services.session_service import SessionService
from backend.config import get_settings
from chatbot.conversation_manager import ConversationManager
from chatbot.llm.gemini_provider import GeminiProvider
from chatbot.interfaces import PlaceholderLLMProvider

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.session_service = SessionService(db)
        self.message_repo = ChatMessageRepository(db)
        
        # Use Gemini when configured; fallback safely to PlaceholderLLMProvider
        # to keep local/test environments usable without credentials.
        settings = get_settings()
        llm_provider = (
            GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL,
            )
            if settings.GEMINI_API_KEY.strip()
            else PlaceholderLLMProvider()
        )
        self.manager = ConversationManager(llm_provider=llm_provider)

    def process_message(
        self,
        session_id: Union[str, uuid.UUID],
        payload: ChatMessageCreate,
        current_user: User,
    ) -> ChatTurnResult:
        """
        Processes a chat message through the frozen MEDHA pipeline.
        """
        # 1. Fetch and validate session ownership
        session_obj = self.session_service.get_session_with_ownership_check(
            session_id, current_user
        )

        if session_obj.status != SessionStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot send message. Session is {session_obj.status}.",
            )

        # 2. Persist the incoming USER message to the database immediately
        user_msg = ChatMessageModel(
            chat_session_id=session_obj.id,
            role="user",
            content=payload.message,
            metadata_payload=payload.metadata,
        )
        self.message_repo.add(user_msg)

        # 3. Mount MedhaState to ConversationManager
        conv_session = attach_to_conversation_manager(self.manager, session_obj)

        # 4. Invoke frozen pipeline
        try:
            turn_result = self.manager.process_message(
                session_id=session_obj.session_identifier,
                message=payload.message,
                language=payload.language,
                behaviour_data=payload.behaviour_data,
                metadata=payload.metadata,
            )
        except Exception as e:
            logger.error(f"ConversationManager error for session {session_obj.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Conversation processing failed.",
            )

        # 5. Extract updated state and sync to snapshot
        updated_state_dict = sync_from_conversation_manager(self.manager, session_obj)
        session_obj.state_snapshot = updated_state_dict
        self.db.commit()

        # 5b. Update unified prediction & Multimodal Fusion with conversational text
        try:
            from backend.services.prediction_service import update_text_prediction
            case_id = session_obj.case_id
            timepoint = session_obj.timepoint or 1
            update_text_prediction(
                self.db,
                case_id=case_id,
                timepoint=timepoint,
                text_content=payload.message,
                session_id=session_obj.id,
                source="chatbot",
            )
        except Exception as pred_err:
            logger.warning(f"Could not update text prediction for chat message: {pred_err}")

        # 6. Persist ASSISTANT message to database
        assistant_metadata = turn_result.metadata.copy() if turn_result.metadata else {}
        if turn_result.safety_result and turn_result.safety_result.is_triggered:
            assistant_metadata["safety_triggered"] = True
            assistant_metadata["category"] = turn_result.safety_result.category

        assistant_msg = ChatMessageModel(
            chat_session_id=session_obj.id,
            role="assistant",
            content=turn_result.assistant_response,
            metadata_payload=assistant_metadata,
        )
        self.message_repo.add(assistant_msg)

        # 7. Return sanitized ChatTurnResult
        safety_triggered = (
            turn_result.safety_result.is_triggered if turn_result.safety_result else False
        )

        return ChatTurnResult(
            session_id=str(session_obj.id),
            turn_index=turn_result.turn_index,
            user_message=turn_result.user_message,
            assistant_response=turn_result.assistant_response,
            timestamp=assistant_msg.created_at,
            safety_triggered=safety_triggered,
        )

    def get_chat_history(
        self,
        session_id: Union[str, uuid.UUID],
        current_user: User,
    ) -> ChatHistoryResponse:
        """
        Retrieves chronologically ordered messages for an authorized session.
        """
        # Validates ownership implicitly
        session_obj = self.session_service.get_session_with_ownership_check(
            session_id, current_user
        )

        messages = self.message_repo.get_by_session_id(session_obj.id)
        
        message_responses = [
            ChatMessageResponse(
                id=msg.id,
                chat_session_id=msg.chat_session_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at,
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            session_id=session_obj.id,
            messages=message_responses,
        )
