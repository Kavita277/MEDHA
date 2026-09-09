from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.patient_schema import PatientCreate, PatientUpdate, PatientResponse
from app.services import patient_service
from app.services.ai_services import (
    TextService, VoiceService, BehaviourService, 
    StructuredService, TemporalService
)
from app.services.fusion_service import FusionService

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    return patient_service.create_patient(db, patient)

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(patient_id: str, db: Session = Depends(get_db)):
    return patient_service.get_patient(db, patient_id)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, patient_update: PatientUpdate, db: Session = Depends(get_db)):
    return patient_service.update_patient(db, patient_id, patient_update)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient_service.delete_patient(db, patient_id)
    return None

@router.post("/{patient_id}/risk")
def calculate_risk(patient_id: str, db: Session = Depends(get_db)):
    patient = patient_service.get_patient(db, patient_id)
    mock_data = {"data": "mock"}
    text_out = TextService().predict(mock_data)
    voice_out = VoiceService().predict(mock_data)
    behaviour_out = BehaviourService().predict(mock_data)
    structured_out = StructuredService().predict(mock_data)
    temporal_out = TemporalService().predict(mock_data)
    
    fusion_out = FusionService().predict(text_out, voice_out, behaviour_out, structured_out, temporal_out)
    return fusion_out
