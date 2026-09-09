from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.patient import Patient
from app.schemas.patient_schema import PatientCreate, PatientUpdate

def create_patient(db: Session, patient: PatientCreate):
    try:
        db_patient = Patient(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient with this ID already exists.")

def get_patient(db: Session, patient_id: str):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

def update_patient(db: Session, patient_id: str, patient_update: PatientUpdate):
    patient = get_patient(db, patient_id)
    update_data = patient_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient

def delete_patient(db: Session, patient_id: str):
    patient = get_patient(db, patient_id)
    db.delete(patient)
    db.commit()
    return patient
