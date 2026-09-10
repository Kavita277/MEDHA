"""
Check-In Endpoints
==================
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.persistence.database import get_db
from backend.security.dependencies import get_current_user
from backend.services.checkin_service import CheckInService
from backend.schemas.checkin import CheckInResponse, CheckInAnswerRequest, CheckInAnswerResponse
from backend.persistence.models.user import User

router = APIRouter()


@router.post("/sessions/{session_id}", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def start_checkin(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a check-in for the given session. Delegates question selection to the frozen Question Engine.
    """
    service = CheckInService(db)
    return service.start_checkin(session_id, current_user)


@router.get("/{checkin_id}", response_model=CheckInResponse)
def get_checkin(
    checkin_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the state of a check-in.
    """
    service = CheckInService(db)
    return service.get_checkin(checkin_id, current_user)


@router.post("/{checkin_id}/answer", response_model=CheckInAnswerResponse)
def submit_answer(
    checkin_id: uuid.UUID,
    request: CheckInAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an answer to the current check-in question.
    Updates the MedhaState structured features and asks the Question Engine for the next question.
    """
    service = CheckInService(db)
    return service.submit_answer(checkin_id, current_user, request.answer)


@router.post("/{checkin_id}/complete", response_model=CheckInResponse)
def complete_checkin(
    checkin_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually complete the check-in and emit the checkin_completed event.
    """
    service = CheckInService(db)
    return service.complete_checkin(checkin_id, current_user)

