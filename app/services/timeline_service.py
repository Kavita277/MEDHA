from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.history import RiskHistory, InteractionHistory
from app.models.session import Session as PatientSession, Answer
from fastapi import HTTPException

def get_patient_timeline(db: Session, patient_id: str):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    events = []
    
    # 1. Risk Histories
    risks = db.query(RiskHistory).filter(RiskHistory.patient_id == patient_id).all()
    for r in risks:
        events.append({
            "type": "RiskPrediction",
            "timestamp": r.created_at.isoformat(),
            "data": {
                "dds": r.dds,
                "risk_level": r.risk_level,
                "recommendation": r.recommendation
            }
        })
        
    # 2. Interaction Histories
    interactions = db.query(InteractionHistory).filter(InteractionHistory.patient_id == patient_id).all()
    for i in interactions:
        events.append({
            "type": "Interaction",
            "timestamp": i.created_at.isoformat(),
            "data": {
                "interaction_type": i.interaction_type,
                "summary": i.summary,
                "session_id": i.session_id
            }
        })
        
    # 3. Sessions & Answers
    sessions = db.query(PatientSession).filter(PatientSession.patient_id == patient.id).all()
    for s in sessions:
        events.append({
            "type": "Session",
            "timestamp": s.created_at.isoformat(),
            "data": {
                "session_id": s.id,
                "status": s.status
            }
        })
        # Answers within session
        answers = db.query(Answer).filter(Answer.session_id == s.id).all()
        for a in answers:
            events.append({
                "type": "Answer",
                "timestamp": a.created_at.isoformat() if hasattr(a, 'created_at') and a.created_at else s.created_at.isoformat(),
                "data": {
                    "question_id": a.question_id,
                    "answer_text": a.answer_text
                }
            })
            
    # Sort events chronologically
    events.sort(key=lambda x: x["timestamp"])
    
    return {
        "patient": patient,
        "events": events
    }
