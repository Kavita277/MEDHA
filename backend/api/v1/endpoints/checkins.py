"""
Check-In Endpoints
==================
"""

import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks
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


@router.get("/status/today")
def get_today_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if the user has completed or is currently in a check-in today.
    """
    service = CheckInService(db)
    return service.get_today_checkin_status(current_user)


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


from backend.jobs.prediction_queue import enqueue_prediction
from backend.persistence.repositories.session import SessionRepository


@router.post("/{checkin_id}/answer", response_model=CheckInAnswerResponse)
def submit_answer(
    checkin_id: uuid.UUID,
    request: CheckInAnswerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an answer to the current check-in question.
    Updates the MedhaState structured features and asks the Question Engine for the next question.
    """
    service = CheckInService(db)
    res = service.submit_answer(checkin_id, current_user, request.answer)

    # Enqueue background prediction so downstream models process latest data
    session_repo = SessionRepository(db)
    session_obj = session_repo.get(res.checkin.session_id)
    if session_obj:
        background_tasks.add_task(enqueue_prediction, session_obj.case_id, session_obj.timepoint)

    return res


@router.post("/{checkin_id}/complete", response_model=CheckInResponse)
def complete_checkin(
    checkin_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually complete the check-in and emit the checkin_completed event.
    """
    service = CheckInService(db)
    response = service.complete_checkin(checkin_id, current_user)
    
    # Enqueue background prediction
    session_repo = SessionRepository(db)
    session_obj = session_repo.get(response.session_id)
    if session_obj:
        background_tasks.add_task(enqueue_prediction, session_obj.case_id, session_obj.timepoint)
    
    return response

