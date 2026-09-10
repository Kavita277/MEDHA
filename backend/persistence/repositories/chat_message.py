"""
Chat Message Repository
=======================

Data access layer for ChatMessageModel.
"""

from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models.chat_message import ChatMessageModel


class ChatMessageRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add(self, message: ChatMessageModel) -> ChatMessageModel:
        """Adds a new message to the database."""
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_session_id(self, session_id: uuid.UUID) -> List[ChatMessageModel]:
        """Retrieves chronologically ordered messages for a given session."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.chat_session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())
