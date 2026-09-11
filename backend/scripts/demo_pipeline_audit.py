import sys
import uuid
import json
import logging
from fastapi.testclient import TestClient
from backend.main import app
from backend.persistence.database import SessionLocal, engine
from backend.persistence.base import Base
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.security.passwords import hash_password
# Import models to ensure they are registered with Base
import backend.persistence.models.voice_record

logging.basicConfig(level=logging.ERROR)

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    t_user = db.query(User).filter(User.email == "demo.therapist@medha.test").first()
    if not t_user:
        t_user = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Demo Therapist",
            email="demo.therapist@medha.test",
            password_hash=hash_password("TherapistPass2026!"),
            status=UserStatus.ACTIVE,
        )
        db.add(t_user)
        db.flush()
        t_profile = Therapist(id=uuid.uuid4(), user_id=t_user.id, display_name="Demo Therapist")
        db.add(t_profile)
        db.commit()
    return db

def run_audit():
    trace = {}
    db = setup_db()
    client = TestClient(app)

    # 1. Therapist login
    resp = client.post("/api/v1/auth/login", json={"email": "demo.therapist@medha.test", "password": "TherapistPass2026!"})
    if resp.status_code != 200:
        print(f"Therapist login failed: {resp.text}")
        return
    t_token = resp.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}
    trace["therapist_login"] = "PASS"

    # 2. Create case
    patient_email = f"demo.patient.{uuid.uuid4().hex[:6]}@medha.test"
    patient_pwd = "PatientPass2026!"
    victim_id = f"V-DEMO-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/v1/therapist/users", headers=t_headers, json={"name": "Demo Patient", "email": patient_email, "password": patient_pwd, "victim_id": victim_id})
    if resp.status_code != 201:
        print(f"User creation failed: {resp.text}")
        return
    case_id = resp.json()["case"]["id"]
    trace["case_creation"] = "PASS"

    # 3. Patient Login
    resp = client.post("/api/v1/auth/login", json={"email": patient_email, "password": patient_pwd})
    p_token = resp.json()["access_token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}
    trace["patient_login"] = "PASS"

    # 4. Create session
    resp = client.post("/api/v1/sessions", headers=p_headers, json={"session_identifier": f"sess_{uuid.uuid4().hex[:8]}"})
    session_id = resp.json()["id"]
    trace["session_creation"] = {"session_id": session_id}

    # 5. Check-in
    resp = client.post(f"/api/v1/checkins/sessions/{session_id}", headers=p_headers)
    checkin_data = resp.json()
    trace["start_checkin"] = checkin_data
    checkin_id = checkin_data["id"]
    
    resp = client.post(f"/api/v1/checkins/{checkin_id}/answer", headers=p_headers, json={"answer": {"value": 8.0}})
    trace["answer_checkin"] = resp.json()

    resp = client.post(f"/api/v1/checkins/{checkin_id}/complete", headers=p_headers)
    trace["complete_checkin"] = resp.json()

    # 6. Chat message
    resp = client.post(f"/api/v1/chat/sessions/{session_id}/message", headers=p_headers, json={"message": "I feel anxious and overwhelmed by everything happening right now.", "language": "en"})
    trace["chat_message"] = resp.json()

    # 7. Voice checkin
    import io
    import wave
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b'\x00\x00' * 16000)
    wav_io.seek(0)
    wav_io.name = "dummy.wav"

    resp = client.post("/api/v1/voice/checkin", headers=p_headers, data={"timepoint": "Day 1", "session_id": session_id}, files={"audio_file": ("dummy.wav", wav_io, "audio/wav")})
    if resp.status_code == 200:
        trace["voice_checkin"] = resp.json()
    else:
        trace["voice_checkin"] = f"FAIL: {resp.text}"

    # 8. Trigger prediction
    try:
        from backend.services.prediction_service import generate_predictions
        pred_record = generate_predictions(db, uuid.UUID(case_id), timepoint=1)
        
        if pred_record:
            trace["prediction"] = {
                "fusion_dds_prediction": pred_record.fusion_dds_prediction,
                "temporal_risk_score": pred_record.temporal_risk_score,
                "triage_level": pred_record.triage_level,
                "future_escalation_flag": pred_record.future_escalation_flag,
                "components": {
                    "struct_pred": pred_record.struct_pred,
                    "text_pred": pred_record.text_pred,
                    "voice_pred": pred_record.voice_pred,
                    "behav_pred": pred_record.behav_pred
                }
            }
        else:
            trace["prediction"] = "FAIL - generate_predictions returned None"
    except Exception as e:
        trace["prediction"] = f"FAIL - Exception: {e}"

    # 9. Therapist results
    resp = client.get(f"/api/v1/therapist/cases/{case_id}/results", headers=t_headers)
    trace["therapist_results"] = resp.json()

    # 10. Fetch DB session to see state_snapshot
    from backend.persistence.models.session import SessionModel
    sess_model = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    trace["state_snapshot"] = sess_model.state_snapshot if sess_model else None

    # Write output to file
    with open("audit_trace.json", "w") as f:
        json.dump(trace, f, indent=2)
    print("Audit trace written to audit_trace.json")

if __name__ == "__main__":
    run_audit()
