from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List
import time

from app.database import get_db

# Import the pre-initialized adapters from analyze
from app.routers.analyze import (
    text_adapter,
    voice_adapter,
    behaviour_adapter,
    structured_adapter,
    temporal_adapter
)
from app.services.fusion_service import FusionService
from app.services.interaction_service import log_interaction

router = APIRouter(tags=["fusion"])
fusion_service = FusionService()

class FusionRequest(BaseModel):
    text: str
    audio_path: str
    patient_id: str
    behaviour_payload: Dict[str, Any]
    structured_data: Dict[str, Any]
    temporal_features: List[List[float]]

@router.post("/fusion/predict")
def fusion_predict(request: FusionRequest, db: Session = Depends(get_db)):
    start = time.time()
    
    engine_outputs = {}
    
    # 1. Text Engine
    try:
        res = text_adapter.predict(request.text)
        risk = res.get("text_vector", {}).get("text_distress", 0.0)
        engine_outputs["text"] = {"risk_score": risk, "confidence": 1.0, "prediction": res}
    except Exception as e:
        engine_outputs["text"] = {"risk_score": 0.0, "confidence": 0.0, "error": str(e)}

    # 2. Voice Engine
    try:
        res = voice_adapter.predict(request.audio_path)
        risk = res.get("voice_distress", 0.0)
        conf = res.get("confidence", 0.0)
        engine_outputs["voice"] = {"risk_score": risk, "confidence": conf, "prediction": res}
    except Exception as e:
        engine_outputs["voice"] = {"risk_score": 0.0, "confidence": 0.0, "error": str(e)}

    # 3. Behaviour Engine
    try:
        res = behaviour_adapter.predict(request.patient_id, request.behaviour_payload)
        risk = res.get("behavioral_risk_score", 0.0)
        engine_outputs["behaviour"] = {"risk_score": risk, "confidence": 1.0, "prediction": res}
    except Exception as e:
        engine_outputs["behaviour"] = {"risk_score": 0.0, "confidence": 0.0, "error": str(e)}

    # 4. Structured Risk Engine
    try:
        res = structured_adapter.predict(request.structured_data)
        risk = res.get("structured_risk", 0.0)
        engine_outputs["structured"] = {"risk_score": risk, "confidence": 1.0, "prediction": res}
    except Exception as e:
        engine_outputs["structured"] = {"risk_score": 0.0, "confidence": 0.0, "error": str(e)}

    # 5. Temporal Engine
    try:
        res = temporal_adapter.predict(request.temporal_features)
        risk = res.get("temporal_risk_score", 0.0)
        engine_outputs["temporal"] = {"risk_score": risk, "confidence": 1.0, "prediction": res}
    except Exception as e:
        engine_outputs["temporal"] = {"risk_score": 0.0, "confidence": 0.0, "error": str(e)}

    # Fusion
    result = fusion_service.predict(request.patient_id, engine_outputs, db)
    
    # Log the fusion run
    log_interaction(db, request.patient_id, "Fusion", "Complete AI Prediction run")
    
    proc_time = (time.time() - start) * 1000
    result["processing_time_ms"] = round(proc_time, 2)
    
    return result
