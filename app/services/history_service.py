from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.history import RiskHistory
from fastapi import HTTPException

def get_patient_history(db: Session, patient_id: str):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    history = db.query(RiskHistory).filter(RiskHistory.patient_id == patient_id).order_by(RiskHistory.created_at.asc()).all()
    
    return {
        "patient": patient,
        "history": history
    }
