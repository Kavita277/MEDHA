import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from backend.api.v1.endpoints.auth import get_current_user
from backend.persistence.database import get_db
from backend.persistence.models.user import User
from backend.services.case_service import CaseService
from backend.services.voice_service import process_voice_checkin
from backend.schemas.voice import VoiceCheckInResponse

router = APIRouter()

from backend.jobs.prediction_queue import enqueue_prediction

@router.post("/checkin", response_model=VoiceCheckInResponse)
def upload_voice_checkin(
    background_tasks: BackgroundTasks,
    timepoint: str = Form(...),
    session_id: Optional[str] = Form(None),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a voice checkin audio file, processes it through the voice adapter,
    and returns a safe response without exposing internal models.
    """
    # 1. Get the active case for the current user (ensures isolation)
    case = CaseService(db).get_active_case_for_user(current_user.id)
    
    # 2. Process the voice recording
    parsed_session = uuid.UUID(session_id) if session_id else None
    record = process_voice_checkin(db, case, timepoint, audio_file, parsed_session)
    
    # Extract timepoint int
    try:
        t_int = int(timepoint.replace("Day ", ""))
    except Exception:
        t_int = 1

    # Enqueue Prediction
    background_tasks.add_task(enqueue_prediction, case.id, t_int)
    
    return VoiceCheckInResponse.model_validate(record)
