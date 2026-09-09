from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.history_service import get_patient_history
from app.services.trend_service import get_patient_trend
from app.services.timeline_service import get_patient_timeline

router = APIRouter(tags=["history"])

@router.get("/patients/{patient_id}/history")
def read_history(patient_id: str, db: Session = Depends(get_db)):
    return get_patient_history(db, patient_id)

@router.get("/patients/{patient_id}/trend")
def read_trend(patient_id: str, db: Session = Depends(get_db)):
    return get_patient_trend(db, patient_id)

@router.get("/patients/{patient_id}/timeline")
def read_timeline(patient_id: str, db: Session = Depends(get_db)):
    return get_patient_timeline(db, patient_id)
