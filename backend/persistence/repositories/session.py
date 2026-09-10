"""
Session Repository
==================

Data access methods for SessionModel records (table chat_sessions).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.repositories import BaseRepository


class SessionRepository(BaseRepository[SessionModel]):
    """Repository handling CRUD operations and queries for SessionModel entities."""

    def __init__(self, db: Session):
        super().__init__(SessionModel, db)

    def get_by_identifier(self, session_identifier: str) -> Optional[SessionModel]:
        """Finds a session by unique string session_identifier (e.g. 'sess_...')."""
        statement = (
            select(SessionModel)
            .options(joinedload(SessionModel.case))
            .where(SessionModel.session_identifier == session_identifier)
        )
        return self.db.scalars(statement).first()

    def get_by_id_or_identifier(self, session_id: Union[str, uuid.UUID]) -> Optional[SessionModel]:
        """
        Flexible lookup attempting resolution by UUID primary key first,
        falling back to session_identifier string lookup.
        """
        # If already a UUID object
        if isinstance(session_id, uuid.UUID):
            statement = (
                select(SessionModel)
                .options(joinedload(SessionModel.case))
                .where(SessionModel.id == session_id)
            )
            return self.db.scalars(statement).first()

        clean_str = str(session_id).strip()
        # Check if clean_str is valid UUID format
        try:
            parsed_uuid = uuid.UUID(clean_str)
            statement = (
                select(SessionModel)
                .options(joinedload(SessionModel.case))
                .where(SessionModel.id == parsed_uuid)
            )
            found = self.db.scalars(statement).first()
            if found:
                return found
        except (ValueError, AttributeError):
            pass

        # Fallback to session_identifier
        return self.get_by_identifier(clean_str)

    def list_for_case(self, case_id: uuid.UUID) -> List[SessionModel]:
        """Lists all sessions belonging to a specific case, ordered most recent first."""
        statement = (
            select(SessionModel)
            .where(SessionModel.case_id == case_id)
            .order_by(SessionModel.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_active_session_for_case(self, case_id: uuid.UUID) -> Optional[SessionModel]:
        """Finds the current active session for a given case, if one exists."""
        statement = (
            select(SessionModel)
            .where(
                SessionModel.case_id == case_id,
                SessionModel.status == SessionStatus.ACTIVE.value,
            )
            .order_by(SessionModel.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def update_snapshot(self, session_obj: SessionModel, snapshot: Dict[str, Any]) -> SessionModel:
        """Updates the stored MedhaState JSON snapshot."""
        session_obj.state_snapshot = snapshot
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj

    def close_session(self, session_obj: SessionModel) -> SessionModel:
        """Transitions session to ENDED and records closed_at timestamp."""
        session_obj.status = SessionStatus.ENDED.value
        session_obj.closed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj
