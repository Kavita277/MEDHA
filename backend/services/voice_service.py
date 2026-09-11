import logging
import os
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from chatbot.state.medha_state import MedhaState
from chatbot.engines.voice_adapter import MedhaVoiceAdapter
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.case import Case
from backend.services.prediction_service import update_voice_prediction

logger = logging.getLogger(__name__)

def process_voice_checkin(
    db: Session,
    case: Case,
    timepoint: str,
    audio_file: UploadFile,
    session_id: Optional[str] = None
) -> VoiceRecordModel:
    """
    Processes the voice check-in:
      Voice Recording -> Upload -> Voice Service -> Feature Extraction
      -> Voice Model -> voice_score -> Update PredictionResult -> Fusion Pipeline.
    Stores recording metadata, extracted features, transcript, and voice_score.
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
        orig_filename = audio_file.filename or "recording.wav"
        suffix = os.path.splitext(orig_filename)[1] if orig_filename else ".wav"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)

        # Estimate duration if possible
        duration_seconds = None
        try:
            import wave
            with wave.open(temp_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration_seconds = round(frames / float(rate), 2)
        except Exception:
            try:
                # File size approximation for 16-bit 16kHz mono audio (~32KB/sec)
                file_size = os.path.getsize(temp_path)
                duration_seconds = round(max(1.0, file_size / 32000.0), 2)
            except Exception:
                duration_seconds = 10.0

        # 2. Restore MedhaState from session or create initial state
        if db_session and db_session.state_snapshot:
            state = restore_medha_state(db_session.state_snapshot)
        else:
            state = create_initial_medha_state(
                victim_id=case.victim_id,
                session_id=str(session_id) if session_id else None
            )
        
        # 3. Invoke MedhaVoiceAdapter for feature extraction
        adapter = MedhaVoiceAdapter()
        adapter.process_and_update_state(state, temp_path)

        # 4. Optional transcript generation
        transcript = "Voice reflection recorded: Audio analyzed for clinical acoustic prosody."
        try:
            if hasattr(adapter, "transcribe") and callable(adapter.transcribe):
                res = adapter.transcribe(temp_path)
                if isinstance(res, str):
                    transcript = res
        except Exception:
            pass

        # 5. Persist updated MedhaState back to the session
        if db_session:
            db_session.state_snapshot = serialize_medha_state(state)
            db.add(db_session)

        # Parse numeric timepoint
        try:
            t_int = int(str(timepoint).replace("Day ", "").replace("T", "").strip())
        except Exception:
            t_int = case.current_timepoint or 1

        # 6. Execute Voice Model -> voice_score -> Unified PredictionResult -> Fusion Pipeline
        parsed_session_id = db_session.id if db_session else None
        voice_score = None
        try:
            pred_record = update_voice_prediction(
                db=db,
                case_id=case.id,
                timepoint=t_int,
                voice_features=state.voice_features,
                session_id=parsed_session_id,
            )
            voice_score = pred_record.voice_score
        except Exception as e:
            logger.warning(f"Voice prediction update error: {e}")

        available = state.voice_available if state.voice_available is not None else 0.0

        # 7. Persist complete VoiceRecordModel for future analysis and therapist review
        now = datetime.now(timezone.utc)
        record = VoiceRecordModel(
            case_id=case.id,
            session_id=parsed_session_id,
            timepoint=str(timepoint),
            audio_filename=orig_filename,
            duration_seconds=duration_seconds,
            extracted_features=state.voice_features,
            transcript=transcript,
            voice_score=voice_score,
            processed_at=now,
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
        # Securely delete the temporary raw audio file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
