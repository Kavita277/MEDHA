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
    temp_path = None
    try:
        # 1. Save uploaded audio to a temporary file
        suffix = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".wav"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)

        # 2. Invoke MedhaVoiceAdapter
        # For the purpose of voice adapter, we instantiate an empty state.
        # In a real integrated flow, this might pull the current MedhaState from DB.
        state = MedhaState()
        
        adapter = MedhaVoiceAdapter()
        adapter.process_and_update_state(state, temp_path)

        # 3. Persist metadata into voice_records
        available = state.modality_availability.get("voice", 0.0)
        
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
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

    finally:
        # 4. Securely delete the temporary raw audio file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
