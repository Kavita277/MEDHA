"""
Session Service
===============

Domain service coordinating session lifecycle, ownership validation, and MedhaState persistence.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.integrations.session_state_adapter import (
    create_initial_medha_state,
    restore_medha_state,
    serialize_medha_state,
)
from chatbot.state.medha_state import MedhaState
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.user import User, UserRole
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.schemas.session import SessionCreateRequest


class SessionService:
    """Service governing session creation, RBAC authorization, and state persistence."""

    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.case_repo = CaseRepository(db)
        self.therapist_repo = TherapistRepository(db)

    def create_session(
        self,
        current_user: User,
        payload: SessionCreateRequest,
    ) -> SessionModel:
        """
        Creates a new conversation session associated with the target case.
        Enforces case ownership:
        - USER role: automatically associates session with user's active case.
        - THERAPIST role: requires case_id and verifies case assignment.
        """
        # 1. Resolve target case
        if current_user.role == UserRole.USER:
            case = self.case_repo.get_active_case_for_user(current_user.id)
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active case found for the current patient user.",
                )
        elif current_user.role == UserRole.THERAPIST:
            if not payload.case_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="case_id is required when a therapist creates a session.",
                )
            case = self.case_repo.get(payload.case_id)
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Case with ID '{payload.case_id}' not found.",
                )
            therapist = self.therapist_repo.get_by_user_id(current_user.id)
            if not therapist or case.therapist_id != therapist.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You may only create sessions for cases assigned to you.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized role for session creation.",
            )

        # 2. Determine session identifier
        if payload.session_identifier:
            sid = payload.session_identifier.strip()
            if self.session_repo.get_by_identifier(sid):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session identifier '{sid}' already exists.",
                )
        else:
            sid = f"sess_{uuid.uuid4().hex[:12]}"

        # 3. Initialize fresh runtime MedhaState
        initial_state = create_initial_medha_state(
            victim_id=case.victim_id,
            session_id=sid,
            timepoint=case.current_timepoint,
        )

        # 4. Persist database record
        session_obj = SessionModel(
            id=uuid.uuid4(),
            case_id=case.id,
            session_identifier=sid,
            timepoint=case.current_timepoint,
            status=SessionStatus.ACTIVE.value,
            state_snapshot=serialize_medha_state(initial_state),
        )
        self.session_repo.add(session_obj)

        # Attach case for eager loading
        session_obj.case = case
        return session_obj

    def get_session_with_ownership_check(
        self,
        session_id: Union[str, uuid.UUID],
        current_user: User,
    ) -> SessionModel:
        """
        Retrieves a session and strictly validates that:
        - A USER may only access sessions belonging to their own case.
        - A THERAPIST may only access sessions belonging to their assigned cases.
        """
        session_obj = self.session_repo.get_by_id_or_identifier(session_id)
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )

        case = session_obj.case
        if not case:
            case = self.case_repo.get(session_obj.case_id)
            session_obj.case = case

        # RBAC ownership enforcement
        if current_user.role == UserRole.USER:
            if case.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You may only access sessions belonging to your own case.",
                )
        elif current_user.role == UserRole.THERAPIST:
            therapist = self.therapist_repo.get_by_user_id(current_user.id)
            if not therapist or case.therapist_id != therapist.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You may only access sessions belonging to your assigned cases.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this session.",
            )

        return session_obj

    def restore_session_state(
        self,
        session_id: Union[str, uuid.UUID],
        current_user: User,
    ) -> MedhaState:
        """
        Retrieves the session with ownership verification and restores
        the complete in-memory MedhaState instance from the stored snapshot.
        """
        session_obj = self.get_session_with_ownership_check(session_id, current_user)
        if session_obj.state_snapshot:
            return restore_medha_state(session_obj.state_snapshot)

        return create_initial_medha_state(
            victim_id=session_obj.case.victim_id,
            session_id=session_obj.session_identifier,
            timepoint=session_obj.timepoint,
        )

    def close_session(
        self,
        session_id: Union[str, uuid.UUID],
        current_user: User,
    ) -> SessionModel:
        """
        Closes an active session, setting status to ENDED and recording closed_at timestamp.
        """
        session_obj = self.get_session_with_ownership_check(session_id, current_user)
        if session_obj.status == SessionStatus.ENDED.value:
            return session_obj

        return self.session_repo.close_session(session_obj)

    def update_session_state(
        self,
        session_id: Union[str, uuid.UUID],
        state: MedhaState,
        current_user: User,
    ) -> SessionModel:
        """
        Persists an updated MedhaState snapshot to the database.
        """
        session_obj = self.get_session_with_ownership_check(session_id, current_user)
        snapshot = serialize_medha_state(state)
        return self.session_repo.update_snapshot(session_obj, snapshot)
