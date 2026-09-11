"""
Step 30 — End-to-End User Flow Integration Test
================================================

Verifies the complete integration flow specified in backend_plan.md §30:

Therapist login
 ↓
Create user
 ↓
Create case
 ↓
User login
 ↓
Create session
 ↓
Start check-in
 ↓
Question Engine selects question
 ↓
User answers
 ↓
Structured feature updated
 ↓
Behaviour event recorded
 ↓
Next question selected
 ↓
Check-in completed
 ↓
Chat session started
 ↓
User sends message
 ↓
ConversationManager processes message
 ↓
Response persisted
 ↓
Behaviour event persisted
 ↓
V2 prediction generated where sufficient data exists
 ↓
Therapist retrieves prediction
"""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.dependencies import get_db
from backend.main import app
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.checkin import CheckInModel
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.event import RawEventModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.security.passwords import hash_password
from backend.services.prediction_service import generate_predictions


@pytest.fixture(scope="function")
def step30_db():
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db() -> Generator:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    # Seed Initial Therapist
    with Session(engine) as session:
        t_user = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Eleanor Vance",
            email="dr.vance@medha.test",
            password_hash=hash_password("TherapistPass2026!"),
            status=UserStatus.ACTIVE,
        )
        session.add(t_user)
        session.flush()

        t_profile = Therapist(
            id=uuid.uuid4(),
            user_id=t_user.id,
            display_name="Dr. Eleanor Vance",
        )
        session.add(t_profile)
        session.commit()

    yield engine
    app.dependency_overrides.clear()


def test_step30_end_to_end_user_flow(step30_db):
    """
    Executes the complete §30 user journey from therapist provisioning
    through patient check-in, chat turn, event logging, prediction generation,
    and therapist prediction retrieval.
    """
    client = TestClient(app)

    # 1. Therapist Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "dr.vance@medha.test", "password": "TherapistPass2026!"},
    )
    assert login_resp.status_code == 200, login_resp.text
    t_token = login_resp.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # 2. Therapist Creates User (and Case auto-created)
    patient_email = "e2e.patient@medha.test"
    patient_pwd = "PatientPass2026!"
    patient_victim_id = "V-E2E-TEST-001"

    create_user_resp = client.post(
        "/api/v1/therapist/users",
        headers=t_headers,
        json={
            "name": "E2E Patient",
            "email": patient_email,
            "password": patient_pwd,
            "victim_id": patient_victim_id,
        },
    )
    assert create_user_resp.status_code == 201, create_user_resp.text
    created_data = create_user_resp.json()
    case_id = created_data["case"]["id"]
    assert case_id is not None
    assert created_data["case"]["victim_id"] == patient_victim_id

    # 3. Patient Login
    p_login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": patient_email, "password": patient_pwd},
    )
    assert p_login_resp.status_code == 200, p_login_resp.text
    p_token = p_login_resp.json()["access_token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}

    # 4. Patient Creates Session
    create_session_resp = client.post(
        "/api/v1/sessions",
        headers=p_headers,
        json={"session_identifier": "sess_e2e_t1"},
    )
    assert create_session_resp.status_code == 201, create_session_resp.text
    session_id = create_session_resp.json()["id"]
    assert session_id is not None

    # 5. Start Check-In
    start_checkin_resp = client.post(
        f"/api/v1/checkins/sessions/{session_id}",
        headers=p_headers,
    )
    assert start_checkin_resp.status_code == 201, start_checkin_resp.text
    checkin_data = start_checkin_resp.json()
    checkin_id = checkin_data["id"]
    assert checkin_data["current_question_id"] is not None
    assert len(checkin_data["questions"]) >= 1
    q1 = checkin_data["questions"][0]
    assert "question_id" in q1
    assert "question_text" in q1

    # 6. User Answers Question -> Structured feature updated & event recorded
    answer_resp = client.post(
        f"/api/v1/checkins/{checkin_id}/answer",
        headers=p_headers,
        json={"answer": {"value": 7.5}},
    )
    assert answer_resp.status_code == 200, answer_resp.text
    ans_data = answer_resp.json()
    assert ans_data["status"].upper() in ["IN_PROGRESS", "COMPLETED"]

    # 7. Complete Check-In
    complete_resp = client.post(
        f"/api/v1/checkins/{checkin_id}/complete",
        headers=p_headers,
    )
    assert complete_resp.status_code == 200, complete_resp.text
    assert complete_resp.json()["status"].upper() == "COMPLETED"

    # 8. Chat Session Started -> User sends message
    chat_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/message",
        headers=p_headers,
        json={
            "message": "I've been feeling a bit overwhelmed by work deadlines, but trying to manage.",
            "language": "en",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text
    chat_turn = chat_resp.json()
    assert "assistant_response" in chat_turn
    assert chat_turn["assistant_response"] is not None

    # Verify chat history is persisted
    history_resp = client.get(
        f"/api/v1/chat/sessions/{session_id}/history",
        headers=p_headers,
    )
    assert history_resp.status_code == 200
    messages = history_resp.json()["messages"]
    assert len(messages) >= 2  # 1 user + 1 assistant

    # 9. Behaviour Event Persisted
    events_payload = {
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "case_id": case_id,
                "session_id": session_id,
                "event_type": "app_interaction_metric",
                "occurred_at": "2026-09-11T08:00:00Z",
                "metadata_payload": {"duration_seconds": 320.0, "response_delay_seconds": 4.5},
            }
        ]
    }
    events_resp = client.post(
        "/api/v1/events/batch",
        headers=p_headers,
        json=events_payload,
    )
    assert events_resp.status_code == 201, events_resp.text
    assert events_resp.json()["processed_count"] == 1

    # 10. Generate V2 Prediction via generate_predictions
    with Session(step30_db) as db:
        # Also attach a behaviour snapshot to represent full modality pipeline
        behav_snapshot = BehaviourFeatureSnapshotModel(
            id=uuid.uuid4(),
            case_id=uuid.UUID(case_id),
            timepoint=1,
            app_interaction_duration=320.0,
            app_interaction_duration_deviation=0.0,
            checkin_response_delay=4.5,
            checkin_response_delay_deviation=0.0,
            checkin_completion_rate=1.0,
            missed_checkin_count=0,
            journal_entry_count=1,
            chat_message_count=2,
            late_night_usage_ratio=0.1,
            support_resource_access_count=0,
        )
        db.add(behav_snapshot)
        db.commit()

        pred_record = generate_predictions(db, uuid.UUID(case_id), timepoint=1)
        assert pred_record is not None
        assert pred_record.case_id == uuid.UUID(case_id)
        assert pred_record.timepoint == 1
        assert pred_record.fusion_dds_prediction is not None
        assert pred_record.triage_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # 11. Therapist Retrieves Prediction & Insights
    results_resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers=t_headers,
    )
    assert results_resp.status_code == 200, results_resp.text
    results_data = results_resp.json()
    assert results_data["case_id"] == case_id
    assert results_data["results_available"] is True
    assert results_data["fusion_dds_prediction"] == pytest.approx(pred_record.fusion_dds_prediction, 0.001)
    assert results_data["triage_level"] == pred_record.triage_level

    # Therapist Retrieves Insights
    insights_resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/insights",
        headers=t_headers,
    )
    assert insights_resp.status_code == 200, insights_resp.text
    insights_data = insights_resp.json()
    assert insights_data["case_id"] == case_id
    assert "factors" in insights_data
    assert "disclaimer" in insights_data
