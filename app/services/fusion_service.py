import json
import math
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.history import RiskHistory

class FusionService:
    def __init__(self):
        # Fallback to deterministic weighted fusion since aby branch lacks the json
        self.weights = {
            "voice": 0.20,
            "behaviour": 0.20,
            "structured": 0.20,
            "temporal": 0.25,
            "text": 0.15
        }

    def predict(self, patient_id: str, engine_outputs: Dict[str, Dict[str, Any]], db: Session) -> Dict[str, Any]:
        engine_scores = {}
        total_confidence = 0.0
        valid_engines = 0
        dds = 0.0
        engine_contributions = {}
        
        # Extract all available scores and confidences
        for engine, out in engine_outputs.items():
            risk_score = out.get("risk_score", 0.0)
            confidence = out.get("confidence", 1.0)
            engine_scores[engine] = risk_score
            total_confidence += confidence
            valid_engines += 1
            
            weight = self.weights.get(engine, 0.0)
            contribution = risk_score * weight * 100
            engine_contributions[engine] = round(contribution, 1)
            dds += contribution
            
        dds = round(dds, 1)
        avg_confidence = round(total_confidence / max(valid_engines, 1), 2)

        # Risk Classification
        if dds < 35:
            risk_level = "LOW"
            recommendations = ["Routine Follow-up"]
        elif dds <= 65:
            risk_level = "MEDIUM"
            recommendations = ["Counselling", "Increase Monitoring"]
        else:
            risk_level = "HIGH"
            recommendations = ["Immediate Counselling", "District Authority Alert", "Witness Protection Review", "Medical Referral"]

        # Save to database
        try:
            history_record = RiskHistory(
                patient_id=patient_id,
                text_score=engine_scores.get("text"),
                voice_score=engine_scores.get("voice"),
                behaviour_score=engine_scores.get("behaviour"),
                structured_score=engine_scores.get("structured"),
                temporal_score=engine_scores.get("temporal"),
                dds=dds,
                risk_level=risk_level,
                confidence=avg_confidence,
                recommendation=recommendations,
                processing_time_ms=0.0
            )
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
        except Exception as e:
            print(f"Failed to save RiskHistory: {e}")
            db.rollback()

        return {
            "dds": dds,
            "risk_level": risk_level,
            "confidence": avg_confidence,
            "engine_scores": engine_scores,
            "engine_contributions": engine_contributions,
            "recommendations": recommendations
        }
