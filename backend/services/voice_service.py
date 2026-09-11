import logging
import os
import tempfile
import shutil
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from chatbot.state.medha_state import MedhaState
from chatbot.engines.voice_adapter import MedhaVoiceAdapter
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.case import Case

logger = logging.getLogger(__name__)

def process_voice_checkin(
    db: Session,
    case: Case,
    timepoint: str,
    audio_file: UploadFile,
    session_id: Optional[str] = None
) -> VoiceRecordModel:
    """
    Processes the voice check-in, runs the voice adapter, 
    and persists the voice record.
    """
    from backend.persistence.repositories.session import SessionRepository
    from backend.integrations.session_state_adapter import (
        restore_medha_state,
        create_initial_medha_state,
        serialize_medha_state
    )

    temp_path = None
    try:
        session_repo = SessionRepository(db)
        db_session = None
        if session_id:
            db_session = session_repo.get_by_id_or_identifier(session_id)

        # 1. Save uploaded audio to a temporary file
        suffix = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".wav"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)

        # 2. Restore MedhaState from session or create initial state
        if db_session and db_session.state_snapshot:
            state = restore_medha_state(db_session.state_snapshot)
        else:
            state = create_initial_medha_state(
                victim_id=case.victim_id,
                session_id=str(session_id) if session_id else None
            )
        
        # 3. Invoke MedhaVoiceAdapter
        adapter = MedhaVoiceAdapter()
        adapter.process_and_update_state(state, temp_path)

        # 4. Persist updated MedhaState back to the session
        if db_session:
            db_session.state_snapshot = serialize_medha_state(state)
            db.add(db_session)

        # 5. Persist metadata into voice_records
        available = state.voice_available if state.voice_available is not None else 0.0
        
        record = VoiceRecordModel(
            case_id=case.id,
            session_id=session_id,
            timepoint=timepoint,
            available=available
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record

    except Exception as e:
        db.rollback()
        logger.error(f"Voice check-in processing failed for case {case.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Voice processing failed.")

    finally:
        # 4. Securely delete the temporary raw audio file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

