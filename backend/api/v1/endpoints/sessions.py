"""
Session Management Endpoints
============================

Provides endpoints for creating, retrieving, and ending conversation sessions:
- POST /api/v1/sessions: Provision a new conversation session
- GET /api/v1/sessions/{session_id}: Retrieve an existing session by UUID or session_identifier
- POST /api/v1/sessions/{session_id}/end: Conclude an active session
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.session import SessionModel
from backend.persistence.models.user import User
from backend.schemas.session import SessionCreateRequest, SessionResponse
from backend.security.dependencies import get_current_user
from backend.services.session_service import SessionService

router = APIRouter()


def _build_session_response(session_obj: SessionModel) -> SessionResponse:
    """Builds a standardized SessionResponse with state summary metadata."""
    state_summary: Optional[Dict[str, Any]] = None
    if session_obj.state_snapshot:
        snap = session_obj.state_snapshot
        history = snap.get("conversation_history", [])
        questions = snap.get("question_history", [])
        state_summary = {
            "turn_count": len(history),
            "questions_asked": len(questions),
            "current_user_message": snap.get("current_user_message"),
            "latest_assistant_response": snap.get("latest_assistant_response"),
            "text_available": snap.get("text_available"),
            "voice_available": snap.get("voice_available"),
        }

    victim_id = session_obj.case.victim_id if session_obj.case else "UNKNOWN"

    return SessionResponse(
        id=session_obj.id,
        case_id=session_obj.case_id,
        victim_id=victim_id,
        session_identifier=session_obj.session_identifier,
        timepoint=session_obj.timepoint,
        status=session_obj.status,
        closed_at=session_obj.closed_at,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
        state_summary=state_summary,
    )


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation Session",
    description="Initializes a new conversation session, links it to an active case, creates an initial MedhaState, and persists it.",
)
def create_session(
    payload: SessionCreateRequest = SessionCreateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Creates a new session for patient or clinician."""
    session_service = SessionService(db)
    session_obj = session_service.create_session(current_user=current_user, payload=payload)
    return _build_session_response(session_obj)


@router.get(
    "",
    response_model=list[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Conversation Sessions",
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SessionResponse]:
    """Lists the authenticated patient's non-empty conversation sessions."""
    session_service = SessionService(db)
    return [
        _build_session_response(session_obj)
        for session_obj in session_service.list_sessions_for_user(current_user)
    ]


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation Session",
    description="Retrieves a session by UUID or session_identifier with strict RBAC case ownership enforcement.",
)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Retrieves session details ensuring patient/therapist case ownership."""
    session_service = SessionService(db)
    session_obj = session_service.get_session_with_ownership_check(session_id=session_id, current_user=current_user)
    return _build_session_response(session_obj)


@router.post(
    "/{session_id}/end",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="End Conversation Session",
    description="Concludes an active session, setting status to ENDED and recording the closed_at timestamp.",
)
def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Concludes an active session."""
    session_service = SessionService(db)
    session_obj = session_service.close_session(session_id=session_id, current_user=current_user)
    return _build_session_response(session_obj)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation Session",
)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Deletes an authorized conversation and its persisted chat messages."""
    session_service = SessionService(db)
    session_service.delete_session(session_id=session_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
