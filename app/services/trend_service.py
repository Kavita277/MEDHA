from sqlalchemy.orm import Session
from app.models.history import RiskHistory
from fastapi import HTTPException
from app.schemas.trend_schema import TrendResponse

def get_patient_trend(db: Session, patient_id: str) -> TrendResponse:
    history = db.query(RiskHistory).filter(RiskHistory.patient_id == patient_id).order_by(RiskHistory.created_at.desc()).all()
    
    if not history:
        return {
            "current_dds": 0.0,
            "average_dds": 0.0,
            "highest_dds": 0.0,
            "lowest_dds": 0.0,
            "trend": "Stable",
            "last_7_predictions": []
        }
        
    dds_values = [h.dds for h in history]
    current = dds_values[0]
    avg = sum(dds_values) / len(dds_values)
    high = max(dds_values)
    low = min(dds_values)
    
    # Simple trend calculation based on first and last if > 1
    if len(dds_values) > 1:
        oldest = dds_values[-1]
        if current > oldest + 5:
            trend = "Increasing"
        elif current < oldest - 5:
            trend = "Decreasing"
        else:
            trend = "Stable"
    else:
        trend = "Stable"
        
    last_7 = history[:7]
    last_7.reverse() # chronological
    
    predictions = []
    for h in last_7:
        predictions.append({
            "date": h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "dds": h.dds,
            "risk": h.risk_level
        })
        
    return {
        "current_dds": round(current, 2),
        "average_dds": round(avg, 2),
        "highest_dds": round(high, 2),
        "lowest_dds": round(low, 2),
        "trend": trend,
        "last_7_predictions": predictions
    }
