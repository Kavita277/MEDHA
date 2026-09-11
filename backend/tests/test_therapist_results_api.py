"""
Step 11: Therapist Results API Tests
=====================================

Tests covering all 15 authorization and functional cases (A–O) from the spec,
plus additional edge cases.

Test Coverage:
  A. Therapist can list own cases.
  B. Therapist cannot list another therapist's cases.
  C. Therapist can retrieve results for own case.
  D. Therapist cannot retrieve another therapist's case results.
  E. Therapist can retrieve session list for own case.
  F. Therapist cannot retrieve another therapist's session list.
  G. Patient cannot access therapist results endpoints.
  H. Unauthenticated user receives 401.
  I. Case with no prediction returns unavailable/null, NOT fabricated zeros.
  J. Missing specialist prediction remains null/unavailable.
  K. Existing available predictions are returned correctly.
  L. Triage value is returned correctly (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN).
  M. Session belonging to a different case cannot bypass authorization.
  N. Result belonging to another case cannot be accessed by ID manipulation.
  O. Regression: all previous tests still pass (import verified by fixture).

  Additional:
  P. Behav_pred is always null (Step 10 blocked).
  Q. Behav_blocked is always True.
  R. results_available=False when no prediction, True when prediction exists.
  S. GET /therapist/sessions/{session_id}/results: correct ownership chain.
  T. GET /therapist/sessions/{session_id}/results: wrong therapist → 403.
"""

import uuid
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.dependencies import get_db
from backend.main import app
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.checkin import CheckInModel, CheckInStatus
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.security.passwords import hash_password


# ===========================================================================
# 1. SHARED TEST FIXTURES
# ===========================================================================

@pytest.fixture(scope="function")
def results_test_db():
    """
    In-memory SQLite database with:
      - Therapist A (with 2 patients: P1, P2)
      - Therapist B (with 1 patient: P3)
      - 1 session per patient (for P1, P2, P3)
      - 1 prediction result for P1 (positive case)
      - P2 has no prediction (unavailable case)
    """
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db() -> Generator:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    with Session(engine) as session:
        # ------------------------------------------------------------------
        # Users
        # ------------------------------------------------------------------
        patient1 = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient One",
            email="p1@medha.test",
            password_hash=hash_password("P1Pass123!"),
            status=UserStatus.ACTIVE,
        )
        patient2 = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Two",
            email="p2@medha.test",
            password_hash=hash_password("P2Pass123!"),
            status=UserStatus.ACTIVE,
        )
        patient3 = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Three",
            email="p3@medha.test",
            password_hash=hash_password("P3Pass123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_user_a = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Alpha",
            email="alpha@medha.test",
            password_hash=hash_password("TherapistA123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_user_b = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Beta",
            email="beta@medha.test",
            password_hash=hash_password("TherapistB123!"),
            status=UserStatus.ACTIVE,
        )
        regular_user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Regular User",
            email="regular@medha.test",
            password_hash=hash_password("Regular123!"),
            status=UserStatus.ACTIVE,
        )

        # ------------------------------------------------------------------
        # Therapist profiles
        # ------------------------------------------------------------------
        therapist_a = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_a.id,
            display_name="Dr. Alpha, MD",
        )
        therapist_b = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_b.id,
            display_name="Dr. Beta, PhD",
        )

        # ------------------------------------------------------------------
        # Cases
        # ------------------------------------------------------------------
        case_p1 = Case(
            id=uuid.uuid4(),
            victim_id="V-P1-001",
            user_id=patient1.id,
            therapist_id=therapist_a.id,
            current_timepoint=3,
            status="active",
        )
        case_p2 = Case(
            id=uuid.uuid4(),
            victim_id="V-P2-001",
            user_id=patient2.id,
            therapist_id=therapist_a.id,
            current_timepoint=1,
            status="active",
        )
        case_p3 = Case(
            id=uuid.uuid4(),
            victim_id="V-P3-001",
            user_id=patient3.id,
            therapist_id=therapist_b.id,
            current_timepoint=2,
            status="active",
        )

        # ------------------------------------------------------------------
        # Sessions
        # ------------------------------------------------------------------
        session_p1 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_p1.id,
            session_identifier="sess_p1_001",
            timepoint=3,
            status=SessionStatus.ENDED.value,
            state_snapshot={
                "conversation_summary": {
                    "important_facts": ["Fact 1"],
                    "current_concerns": ["Concern 1"],
                    "recent_events": [],
                    "support_context": [],
                    "preferences": [],
                    "ongoing_topics": [],
                    "unresolved_topics": [],
                    "important_observations": [],
                },
                "question_history": [
                    {
                        "question_id": "SA-01",
                        "question_text": "Do you feel safe?",
                        "response_text": "Yes",
                        "intent": "safety_support",
                        "asked_at": "2026-09-11T12:28:40.391448+00:00"
                    }
                ]
            }
        )
        session_p2 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_p2.id,
            session_identifier="sess_p2_001",
            timepoint=1,
            status=SessionStatus.ACTIVE.value,
            state_snapshot={} # Missing summary and history
        )
        session_p3 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_p3.id,
            session_identifier="sess_p3_001",
            timepoint=2,
            status=SessionStatus.ACTIVE.value,
        )

        # ------------------------------------------------------------------
        # Prediction result for P1 only (P2 and P3 have NO prediction)
        # ------------------------------------------------------------------
        pred_p1 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_p1.id,
            session_id=session_p1.id,
            timepoint=3,
            fusion_dds_prediction=67.4,
            temporal_risk_score=0.72,
            future_escalation_flag=1,
            triage_level="HIGH",
            struct_pred=65.2,
            text_pred=70.1,
            voice_pred=None,         # voice unavailable (missing != zero)
            behav_pred=None,         # Step 10 blocked
            struct_available=True,
            text_available=True,
            voice_available=False,
            behav_available=False,
            predicted_at=datetime.now(timezone.utc),
        )

        # ------------------------------------------------------------------
        # Checkins, Behaviour Snapshots, Alerts for P1
        # ------------------------------------------------------------------
        checkin_p1 = CheckInModel(
            id=uuid.uuid4(),
            session_id=session_p1.id,
            victim_id="V-P1-001",
            status=CheckInStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
        )
        
        behav_p1 = BehaviourFeatureSnapshotModel(
            id=uuid.uuid4(),
            case_id=case_p1.id,
            timepoint=3,
            app_interaction_duration=120.5,
            checkin_completion_rate=1.0,
            missed_checkin_count=0,
            aggregated_at=datetime.now(timezone.utc),
        )
        
        alert_p1 = SafetyEventModel(
            id=uuid.uuid4(),
            case_id=case_p1.id,
            session_id=session_p1.id,
            event_type="self_harm_intent",
            severity="HIGH",
            status="active",
            detected_at=datetime.now(timezone.utc),
        )

        session.add_all([
            patient1, patient2, patient3,
            therapist_user_a, therapist_user_b,
            regular_user,
            therapist_a, therapist_b,
            case_p1, case_p2, case_p3,
            session_p1, session_p2, session_p3,
            pred_p1,
            checkin_p1, behav_p1, alert_p1,
        ])
        session.commit()

        # Return IDs for use in tests
        yield {
            "engine": engine,
            "therapist_a": {"email": "alpha@medha.test", "password": "TherapistA123!"},
            "therapist_b": {"email": "beta@medha.test", "password": "TherapistB123!"},
            "regular_user": {"email": "regular@medha.test", "password": "Regular123!"},
            "case_p1_id": str(case_p1.id),
            "case_p2_id": str(case_p2.id),
            "case_p3_id": str(case_p3.id),
            "session_p1_id": str(session_p1.id),
            "session_p2_id": str(session_p2.id),
            "session_p3_id": str(session_p3.id),
            "pred_p1_dds": 67.4,
            "pred_p1_risk": 0.72,
            "pred_p1_struct": 65.2,
            "pred_p1_text": 70.1,
        }

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(results_test_db):
    with TestClient(app) as tc:
        yield tc, results_test_db


def _token(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


# ===========================================================================
# 2. TEST CASES (A–O + Additional)
# ===========================================================================

# ---------------------------------------------------------------------------
# A. Therapist can list own cases
# ---------------------------------------------------------------------------
def test_a_therapist_can_list_own_cases(client):
    tc, db = client
    token = _token(tc, "alpha@medha.test", "TherapistA123!")

    resp = tc.get("/api/v1/therapist/cases", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    victim_ids = [c["victim_id"] for c in data]
    assert "V-P1-001" in victim_ids
    assert "V-P2-001" in victim_ids
    # P3 belongs to Therapist B
    assert "V-P3-001" not in victim_ids
    assert len(data) == 2


# ---------------------------------------------------------------------------
# B. Therapist cannot list another therapist's cases
# ---------------------------------------------------------------------------
def test_b_therapist_cannot_see_other_therapist_cases(client):
    tc, db = client
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")

    resp = tc.get("/api/v1/therapist/cases", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    data = resp.json()
    victim_ids = [c["victim_id"] for c in data]
    # Therapist B should only see P3
    assert "V-P3-001" in victim_ids
    assert "V-P1-001" not in victim_ids
    assert "V-P2-001" not in victim_ids
    assert len(data) == 1


# ---------------------------------------------------------------------------
# C. Therapist can retrieve results for own case (P1 — has prediction)
# ---------------------------------------------------------------------------
def test_c_therapist_can_get_own_case_results(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results_available"] is True
    assert data["case_id"] == case_id
    assert data["victim_id"] == "V-P1-001"
    assert data["fusion_dds_prediction"] == pytest.approx(67.4, rel=1e-3)
    assert data["temporal_risk_score"] == pytest.approx(0.72, rel=1e-3)
    assert data["future_escalation_flag"] == 1
    assert data["triage_level"] == "HIGH"


# ---------------------------------------------------------------------------
# D. Therapist cannot retrieve another therapist's case results
# ---------------------------------------------------------------------------
def test_d_therapist_cannot_get_other_therapist_case_results(client):
    tc, db = client
    # P1 belongs to Therapist A; Therapist B must be denied
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# E. Therapist can retrieve session list for own case
# ---------------------------------------------------------------------------
def test_e_therapist_can_list_own_case_sessions(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/sessions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    identifiers = [s["session_identifier"] for s in data]
    assert "sess_p1_001" in identifiers


# ---------------------------------------------------------------------------
# F. Therapist cannot retrieve another therapist's session list
# ---------------------------------------------------------------------------
def test_f_therapist_cannot_list_other_therapist_sessions(client):
    tc, db = client
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    # case_p1 belongs to Therapist A
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/sessions",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# G. Patient cannot access therapist results endpoints
# ---------------------------------------------------------------------------
def test_g_patient_cannot_access_therapist_results_endpoints(client):
    tc, db = client
    # Log in as a regular USER
    user_token = _token(tc, "regular@medha.test", "Regular123!")
    headers = {"Authorization": f"Bearer {user_token}"}
    case_id = db["case_p1_id"]
    session_id = db["session_p1_id"]

    assert tc.get("/api/v1/therapist/cases", headers=headers).status_code == 403
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/results", headers=headers).status_code == 403
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/sessions", headers=headers).status_code == 403
    assert tc.get(f"/api/v1/therapist/sessions/{session_id}/results", headers=headers).status_code == 403


# ---------------------------------------------------------------------------
# H. Unauthenticated user receives 401
# ---------------------------------------------------------------------------
def test_h_unauthenticated_receives_401(client):
    tc, db = client
    case_id = db["case_p1_id"]
    session_id = db["session_p1_id"]

    assert tc.get("/api/v1/therapist/cases").status_code == 401
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/results").status_code == 401
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/sessions").status_code == 401
    assert tc.get(f"/api/v1/therapist/sessions/{session_id}/results").status_code == 401


# ---------------------------------------------------------------------------
# I. Case with no prediction returns unavailable/null, NOT fabricated zeros
# ---------------------------------------------------------------------------
def test_i_case_with_no_prediction_returns_unavailable(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    # P2 has NO prediction record
    case_id = db["case_p2_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["results_available"] is False
    assert data["triage_level"] == "UNKNOWN"

    # All prediction fields MUST be null — not zero, not empty string
    assert data["fusion_dds_prediction"] is None
    assert data["temporal_risk_score"] is None
    assert data["future_escalation_flag"] is None
    assert data["predicted_at"] is None

    specialists = data["specialists"]
    assert specialists["struct_pred"] is None
    assert specialists["text_pred"] is None
    assert specialists["voice_pred"] is None
    assert specialists["behav_pred"] is None
    assert specialists["struct_available"] is False
    assert specialists["text_available"] is False
    assert specialists["voice_available"] is False
    assert specialists["behav_available"] is False


# ---------------------------------------------------------------------------
# J. Missing specialist prediction (voice) remains null
# ---------------------------------------------------------------------------
def test_j_missing_specialist_prediction_is_null_not_zero(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Voice was intentionally unavailable in the fixture
    specialists = data["specialists"]
    assert specialists["voice_pred"] is None
    assert specialists["voice_available"] is False


# ---------------------------------------------------------------------------
# K. Existing available predictions returned correctly
# ---------------------------------------------------------------------------
def test_k_available_predictions_returned_correctly(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    specialists = data["specialists"]

    assert data["results_available"] is True
    assert data["fusion_dds_prediction"] == pytest.approx(db["pred_p1_dds"], rel=1e-3)
    assert data["temporal_risk_score"] == pytest.approx(db["pred_p1_risk"], rel=1e-3)
    assert specialists["struct_pred"] == pytest.approx(db["pred_p1_struct"], rel=1e-3)
    assert specialists["text_pred"] == pytest.approx(db["pred_p1_text"], rel=1e-3)
    assert specialists["struct_available"] is True
    assert specialists["text_available"] is True


# ---------------------------------------------------------------------------
# L. Triage value is returned correctly
# ---------------------------------------------------------------------------
def test_l_triage_value_is_correct(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    # DDS=67.4 >= 50, Risk=0.72 >= 0.50 → HIGH
    assert resp.json()["triage_level"] == "HIGH"


def test_l2_triage_unknown_when_no_prediction(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p2_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert resp.json()["triage_level"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# M. Session belonging to a different case cannot bypass authorization
# ---------------------------------------------------------------------------
def test_m_session_from_different_case_cannot_bypass_auth(client):
    tc, db = client
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    # session_p1 belongs to case_p1 which belongs to Therapist A
    # Therapist B tries to access it by session ID
    session_id = db["session_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/sessions/{session_id}/results",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must be 403 regardless of whether session exists
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# N. Result belonging to another case cannot be accessed by ID manipulation
# ---------------------------------------------------------------------------
def test_n_prediction_from_other_case_not_accessible(client):
    tc, db = client
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    # P1's case belongs to Therapist A; Therapist B tries case_p1 results
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# O. Regression: case list response shape is correct
# ---------------------------------------------------------------------------
def test_o_case_list_response_shape(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")

    resp = tc.get("/api/v1/therapist/cases", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    for case in resp.json():
        assert "case_id" in case
        assert "victim_id" in case
        assert "patient_name" in case
        assert "patient_email" in case
        assert "status" in case
        assert "current_timepoint" in case
        assert "case_created_at" in case
        # Must NOT contain password or auth secrets
        assert "password_hash" not in case
        assert "password" not in case


# ---------------------------------------------------------------------------
# P. behav_pred is always null (Step 10 blocked)
# ---------------------------------------------------------------------------
def test_p_behav_pred_always_null(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["specialists"]["behav_pred"] is None
    assert data["specialists"]["behav_available"] is False


# ---------------------------------------------------------------------------
# Q. behav_blocked is always True
# ---------------------------------------------------------------------------
def test_q_behav_blocked_is_always_true(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")

    # Test on case with prediction
    resp1 = tc.get(
        f"/api/v1/therapist/cases/{db['case_p1_id']}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp1.json()["specialists"]["behav_blocked"] is True

    # Test on case without prediction
    resp2 = tc.get(
        f"/api/v1/therapist/cases/{db['case_p2_id']}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp2.json()["specialists"]["behav_blocked"] is True


# ---------------------------------------------------------------------------
# R. results_available reflects actual state
# ---------------------------------------------------------------------------
def test_r_results_available_flag_semantics(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")

    # P1 has a prediction → True
    resp1 = tc.get(
        f"/api/v1/therapist/cases/{db['case_p1_id']}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp1.json()["results_available"] is True

    # P2 has no prediction → False
    resp2 = tc.get(
        f"/api/v1/therapist/cases/{db['case_p2_id']}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp2.json()["results_available"] is False


# ---------------------------------------------------------------------------
# S. Session result endpoint works correctly for own session
# ---------------------------------------------------------------------------
def test_s_therapist_can_get_own_session_results(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    session_id = db["session_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/sessions/{session_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results_available"] is True
    assert data["case_id"] == db["case_p1_id"]


# ---------------------------------------------------------------------------
# T. Wrong therapist cannot use session endpoint
# ---------------------------------------------------------------------------
def test_t_wrong_therapist_cannot_get_session_results(client):
    tc, db = client
    # session_p1 belongs to Therapist A's case; Therapist B must get 403
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    session_id = db["session_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/sessions/{session_id}/results",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# U. Therapist can get historical checkins, behaviour, alerts
# ---------------------------------------------------------------------------
def test_u_therapist_can_get_history_and_alerts(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    # Checkins
    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/checkins",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["timepoint"] == 3

    # Behaviour
    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/behaviour",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["app_interaction_duration"] == 120.5

    # Alerts
    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/alerts",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["event_type"] == "self_harm_intent"


# ---------------------------------------------------------------------------
# V. Wrong therapist cannot get history/alerts
# ---------------------------------------------------------------------------
def test_v_wrong_therapist_cannot_get_history_and_alerts(client):
    tc, db = client
    token_b = _token(tc, "beta@medha.test", "TherapistB123!")
    case_id = db["case_p1_id"]

    assert tc.get(f"/api/v1/therapist/cases/{case_id}/checkins", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/behaviour", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403
    assert tc.get(f"/api/v1/therapist/cases/{case_id}/alerts", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403


# ---------------------------------------------------------------------------
# Triage Service Unit Tests (isolated from HTTP layer)
# ---------------------------------------------------------------------------

def test_triage_critical_dds():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(75.0, None) == "CRITICAL"
    assert compute_triage_level(100.0, 0.0) == "CRITICAL"


def test_triage_critical_risk():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(None, 0.85) == "CRITICAL"
    assert compute_triage_level(10.0, 0.90) == "CRITICAL"


def test_triage_high():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(50.0, None) == "HIGH"
    assert compute_triage_level(None, 0.50) == "HIGH"
    assert compute_triage_level(60.0, 0.40) == "HIGH"


def test_triage_medium():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(25.0, None) == "MEDIUM"
    assert compute_triage_level(None, 0.25) == "MEDIUM"


def test_triage_low():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(10.0, 0.10) == "LOW"
    assert compute_triage_level(24.9, 0.24) == "LOW"


def test_triage_unknown():
    from backend.services.triage_service import compute_triage_level
    assert compute_triage_level(None, None) == "UNKNOWN"

# ---------------------------------------------------------------------------
# Patient Context Tests (Step 14)
# ---------------------------------------------------------------------------
def test_therapist_receives_patient_context(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p1_id"]

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "patient_context" in data
    assert data["patient_context"] is not None
    
    summary = data["patient_context"]["conversation_summary"]
    assert summary is not None
    assert summary["important_facts"] == ["Fact 1"]
    assert summary["current_concerns"] == ["Concern 1"]
    
    history = data["patient_context"]["checkin_responses"]
    assert len(history) == 1
    assert history[0]["question_id"] == "SA-01"
    assert history[0]["question_text"] == "Do you feel safe?"
    assert history[0]["response_text"] == "Yes"
    assert history[0]["intent"] == "safety_support"
    assert history[0]["timestamp"] == "2026-09-11T12:28:40.391448Z"

def test_missing_patient_context_does_not_crash(client):
    tc, db = client
    token_a = _token(tc, "alpha@medha.test", "TherapistA123!")
    case_id = db["case_p2_id"] # Has empty state_snapshot

    resp = tc.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_context"] is None


def test_triage_one_signal_unavailable():
    from backend.services.triage_service import compute_triage_level
    # Only DDS available and below LOW threshold
    assert compute_triage_level(10.0, None) == "LOW"
    # Only risk available and below LOW threshold
    assert compute_triage_level(None, 0.10) == "LOW"
    # Only DDS available, above MEDIUM
    assert compute_triage_level(30.0, None) == "MEDIUM"
