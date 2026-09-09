from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import os
import shutil
import uuid

from app.database import get_db
from app.integrations.text_adapter import TextAdapter
from app.integrations.voice_adapter import VoiceAdapter
from app.integrations.behaviour_adapter import BehaviourAdapter
from app.integrations.structured_adapter import StructuredAdapter
from app.integrations.temporal_adapter import TemporalAdapter
from app.services.interaction_service import log_interaction

router = APIRouter(tags=["analyze"])

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    # Save file to a temporary location to be analyzed
    payloads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tests/payloads"))
    os.makedirs(payloads_dir, exist_ok=True)
    
    file_path = os.path.join(payloads_dir, f"recording_{uuid.uuid4()}.wav")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return absolute path so it can be sent to /analyze/voice
    return {"audio_path": file_path.replace("\\", "/")}

# Load adapters globally
text_adapter = TextAdapter()
voice_adapter = VoiceAdapter()
behaviour_adapter = BehaviourAdapter()
structured_adapter = StructuredAdapter()
temporal_adapter = TemporalAdapter()

class TextRequest(BaseModel):
    text: str
    patient_id: Optional[str] = None

class VoiceRequest(BaseModel):
    audio_path: str
    patient_id: Optional[str] = None

class BehaviourRequest(BaseModel):
    patient_id: str
    payload: Dict[str, Any]

class StructuredRequest(BaseModel):
    data: Dict[str, Any]
    patient_id: Optional[str] = None

class TemporalRequest(BaseModel):
    features: List[List[float]]
    patient_id: Optional[str] = None

def standardize_output(engine_name: str, risk_score: float, confidence: float, prediction: dict, metadata: dict, processing_time_ms: float):
    return {
        "engine": engine_name,
        "risk_score": risk_score,
        "confidence": confidence,
        "prediction": prediction,
        "metadata": metadata,
        "processing_time_ms": processing_time_ms
    }

@router.post("/analyze/text")
def analyze_text(request: TextRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        res = text_adapter.predict(request.text)
        risk = res.get("text_vector", {}).get("text_distress", 0.0)
        proc_time = (time.time() - start) * 1000
        
        if request.patient_id:
            log_interaction(db, request.patient_id, "Text", request.text[:100])
            
        return standardize_output("TextEngine", risk, 1.0, res, {}, proc_time)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/voice")
def analyze_voice(request: VoiceRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        res = voice_adapter.predict(request.audio_path)
        risk = res.get("voice_distress", 0.0)
        conf = res.get("confidence", 0.0)
        proc_time = (time.time() - start) * 1000
        
        if request.patient_id:
            log_interaction(db, request.patient_id, "Voice", f"Audio upload: {request.audio_path}")
            
        return standardize_output("VoiceEngine", risk, conf, res, {}, proc_time)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, TypeError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/behaviour")
def analyze_behaviour(request: BehaviourRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        res = behaviour_adapter.predict(request.patient_id, request.payload)
        risk = res.get("behavioral_risk_score", 0.0)
        proc_time = (time.time() - start) * 1000
        
        log_interaction(db, request.patient_id, "Behaviour", "Behaviour questionnaire submitted")
            
        return standardize_output("BehaviourEngine", risk, 1.0, res, {}, proc_time)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/structured")
def analyze_structured(request: StructuredRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        res = structured_adapter.predict(request.data)
        risk = res.get("structured_risk", 0.0)
        proc_time = (time.time() - start) * 1000
        
        if request.patient_id:
            log_interaction(db, request.patient_id, "Structured", "Structured risk data submitted")
            
        return standardize_output("StructuredEngine", risk, 1.0, res, {}, proc_time)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/temporal")
def analyze_temporal(request: TemporalRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        res = temporal_adapter.predict(request.features)
        risk = res.get("temporal_risk_score", 0.0)
        proc_time = (time.time() - start) * 1000
        
        if request.patient_id:
            log_interaction(db, request.patient_id, "Temporal", "Temporal data generated")
            
        return standardize_output("TemporalEngine", risk, 1.0, res, {}, proc_time)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health endpoints
@router.get("/health/text")
def health_text():
    if text_adapter.engine:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "error", "model_loaded": False, "error": text_adapter.error}

@router.get("/health/voice")
def health_voice():
    if voice_adapter.engine:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "error", "model_loaded": False, "error": voice_adapter.error}

@router.get("/health/behaviour")
def health_behaviour():
    if behaviour_adapter.score_one_day:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "error", "model_loaded": False, "error": behaviour_adapter.error}

@router.get("/health/structured")
def health_structured():
    if structured_adapter.engine:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "error", "model_loaded": False, "error": structured_adapter.error}

@router.get("/health/temporal")
def health_temporal():
    if temporal_adapter.predict_risk:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "error", "model_loaded": False, "error": temporal_adapter.error}
