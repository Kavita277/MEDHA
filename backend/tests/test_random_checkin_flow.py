import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.dependencies import get_db
from backend.config import Settings
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.security.passwords import hash_password

@pytest.fixture(scope="function")
def db_session():
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()

    import uuid
    # Seed therapist, case, patient
    therapist_user = User(
        id=uuid.uuid4(),
        email="th_test@medha.org",
        password_hash=hash_password("TherapistPass123!"),
        role=UserRole.THERAPIST.value,
        status=UserStatus.ACTIVE.value,
        name="Dr. Test",
    )
    db.add(therapist_user)
    db.flush()

    therapist = Therapist(id=uuid.uuid4(), user_id=therapist_user.id, display_name="Dr. Test")
    db.add(therapist)
    db.flush()

    patient_user = User(
        id=uuid.uuid4(),
        email="patient_checkin@medha.org",
        password_hash=hash_password("PatientPass123!"),
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
        name="Test Patient",
    )
    db.add(patient_user)
    db.flush()

    case = Case(id=uuid.uuid4(), therapist_id=therapist.id, user_id=patient_user.id, victim_id="V_CHECKIN_TEST")
    db.add(case)
    patient_user.case_id = case.id
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield db

    db.close()
    app.dependency_overrides.clear()

def test_random_10_to_15_checkin_flow(db_session):
    client = TestClient(app)

    # 1. Login patient
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "patient_checkin@medha.org", "password": "PatientPass123!"}
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check today-status endpoint
    today_resp = client.get("/api/v1/checkins/status/today", headers=headers)
    assert today_resp.status_code == 200, today_resp.text
    today_data = today_resp.json()
    assert "completed_today" in today_data
    assert today_data["completed_today"] is False
    assert today_data["status"] == "PENDING"

    # 3. Create session
    sess_resp = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"session_identifier": "sess_checkin_flow_01"}
    )
    assert sess_resp.status_code == 201, sess_resp.text
    session_id = sess_resp.json()["id"]

    # 4. Start checkin
    start_resp = client.post(f"/api/v1/checkins/sessions/{session_id}", headers=headers)
    assert start_resp.status_code == 201, start_resp.text
    checkin_data = start_resp.json()
    checkin_id = checkin_data["id"]
    questions = checkin_data["questions"]

    # Verify 10 to 15 questions generated
    assert 10 <= len(questions) <= 15, f"Expected 10-15 questions, got {len(questions)}"
    assert checkin_data["current_question_id"] is not None

    # Verify representation of clinical domains
    q_ids = [q["question_id"] for q in questions]
    prefixes = set(qid.split("-")[0] for qid in q_ids)
    assert "SA" in prefixes, "Safety domain must be represented"
    assert "ES" in prefixes, "Stress domain must be represented"
    assert "SF" in prefixes, "Sleep domain must be represented"
    assert "SE" in prefixes, "Social domain must be represented"
    assert "GW" in prefixes, "Wellbeing domain must be represented"

    # 5. Answer questions sequentially
    current_q_id = checkin_data["current_question_id"]
    answered_count = 0

    while current_q_id and answered_count < len(questions):
        ans_resp = client.post(
            f"/api/v1/checkins/{checkin_id}/answer",
            headers=headers,
            json={"answer": {"value": "4 - Good"}}
        )
        assert ans_resp.status_code == 200, ans_resp.text
        ans_data = ans_resp.json()
        answered_count += 1

        next_q = ans_data.get("next_question")
        if next_q:
            current_q_id = next_q["question_id"]
        else:
            current_q_id = None

    assert answered_count == len(questions), f"Expected to answer {len(questions)} questions, answered {answered_count}"
    assert ans_data["status"] == "COMPLETED"

    # 6. Check today-status endpoint again -> should now reflect completed
    today_after = client.get("/api/v1/checkins/status/today", headers=headers)
    assert today_after.status_code == 200
    assert today_after.json()["completed_today"] is True
    assert today_after.json()["status"] == "COMPLETED"

    # 7. Verify in DB that prediction result was updated with structured score
    pred = db_session.query(PredictionResultModel).first()
    assert pred is not None, "PredictionResult record must exist"
    assert pred.structured_score is not None, "structured_score must be computed"
    assert pred.struct_available is True, "struct_available must be True"
    assert pred.fusion_score is not None, "fusion_score must be computed"
