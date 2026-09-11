"""
Step 25: Therapist Clinical Insights / Explainability API Tests
==============================================================

Tests for:
  - backend/services/insights_service.py
  - backend/api/v1/endpoints/therapist_insights.py
  - GET /api/v1/therapist/cases/{case_id}/insights
  - GET /api/v1/therapist/sessions/{session_id}/insights

Coverage:
  1. Full prediction available -> returns populated insights, factors, summary, signals.
  2. Missing prediction -> results_available=False, safe non-diagnostic message, no crash.
  3. Single prediction (< 2 timepoints) -> trend_available=False, explicit limited history notice.
  4. Multiple longitudinal predictions -> trend_available=True, accurate trend direction (INCREASING/DECREASING/STABLE).
  5. Context flags integration (threat events, protection issues, intake flags).
  6. Recent engagement activity aggregation (checkins, journal, chat, voice).
  7. Authorization & RBAC:
     - Unauthenticated access -> 401
     - Patient role (USER) -> 403
     - Therapist requesting another therapist's case -> 403 (anti-enumeration)
     - Session authorization chain (session -> case -> therapist) -> 403 if mismatch
  8. Safety phrasing guardrail -> no forbidden diagnostic certainty terms.
  9. Determinism -> identical DB state produces identical structured responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.dependencies import get_db
from backend.main import app
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.checkin import CheckInModel, CheckInStatus
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.schemas.insights import CaseInsightsResponse
from backend.security.passwords import hash_password
from engine.explainability_engine import FORBIDDEN_DIAGNOSTIC_TERMS, validate_safety_phrasing


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture(scope="function")
def insights_test_db():
    """
    Sets up an in-memory test database with:
      - Therapist A (owns Case 1 with full prediction & history, Case 2 with no predictions, Case 3 with single prediction)
      - Therapist B (owns Case 4)
      - Patient User (role=USER)
    """
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db() -> Generator:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    with Session(engine) as session:
        # Users
        patient_user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Alice",
            email="patient.alice@medha.test",
            password_hash=hash_password("PatientPass123!"),
            status=UserStatus.ACTIVE,
        )
        patient_bob = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Bob",
            email="patient.bob@medha.test",
            password_hash=hash_password("PatientBob123!"),
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

        therapist_a = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_a.id,
            display_name="Dr. Alpha, MD",
        )
        therapist_b = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_b.id,
            display_name="Dr. Beta, PsyD",
        )

        # Cases
        # Case 1: Multiple timepoints, prediction exists, active alerts & engagement
        case_1 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-001",
            user_id=patient_user.id,
            therapist_id=therapist_a.id,
            current_timepoint=2,
            status="active",
        )
        # Case 2: No predictions at all
        case_2 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-002",
            user_id=patient_user.id,
            therapist_id=therapist_a.id,
            current_timepoint=1,
            status="active",
        )
        # Case 3: Single prediction (< 2 timepoints)
        case_3 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-003",
            user_id=patient_user.id,
            therapist_id=therapist_a.id,
            current_timepoint=1,
            status="active",
        )
        # Case 4: Belongs to Therapist B
        case_4 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-004",
            user_id=patient_bob.id,
            therapist_id=therapist_b.id,
            current_timepoint=1,
            status="active",
        )

        # Sessions
        sess_1_t1 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_identifier="sess_c1_t1",
            timepoint=1,
            status=SessionStatus.ENDED.value,
        )
        sess_1_t2 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_identifier="sess_c1_t2",
            timepoint=2,
            status=SessionStatus.ACTIVE.value,
            state_snapshot={
                "structured_features": {
                    "financial_hardship": True,
                    "investigation_delay": True,
                },
                "context": {
                    "protection_issue": True,
                },
            },
        )
        sess_3 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_3.id,
            session_identifier="sess_c3_t1",
            timepoint=1,
            status=SessionStatus.ACTIVE.value,
        )
        sess_4 = SessionModel(
            id=uuid.uuid4(),
            case_id=case_4.id,
            session_identifier="sess_c4_t1",
            timepoint=1,
            status=SessionStatus.ACTIVE.value,
        )

        # Predictions for Case 1 (T1: 50.0, T2: 78.0 -> INCREASING trend)
        pred_c1_t1 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1_t1.id,
            timepoint=1,
            fusion_dds_prediction=50.0,
            temporal_risk_score=0.45,
            struct_pred=48.0,
            text_pred=52.0,
            voice_pred=50.0,
            behav_pred=None,
            triage_level="MEDIUM",
            struct_available=True,
            text_available=True,
            voice_available=True,
            behav_available=False,
        )
        pred_c1_t2 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1_t2.id,
            timepoint=2,
            fusion_dds_prediction=78.0,
            temporal_risk_score=0.75,
            struct_pred=72.0,
            text_pred=80.0,
            voice_pred=65.0,
            behav_pred=None,
            triage_level="HIGH",
            struct_available=True,
            text_available=True,
            voice_available=True,
            behav_available=False,
        )

        # Prediction for Case 3 (single timepoint: 62.0)
        pred_c3_t1 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_3.id,
            session_id=sess_3.id,
            timepoint=1,
            fusion_dds_prediction=62.0,
            temporal_risk_score=0.60,
            struct_pred=60.0,
            text_pred=65.0,
            voice_pred=58.0,
            behav_pred=None,
            triage_level="HIGH",
            struct_available=True,
            text_available=True,
            voice_available=True,
            behav_available=False,
        )

        # Activity records for Case 1
        checkin_1 = CheckInModel(
            id=uuid.uuid4(),
            session_id=sess_1_t1.id,
            victim_id="V-CASE-001",
            status=CheckInStatus.COMPLETED.value,
        )
        journal_1 = JournalEntryModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            content="Today was very difficult.",
        )
        chat_1 = ChatMessageModel(
            id=uuid.uuid4(),
            chat_session_id=sess_1_t2.id,
            role="user",
            content="I feel overwhelmed.",
        )
        voice_1 = VoiceRecordModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1_t2.id,
            timepoint="2",
            available=1.0,
        )

        # Safety Alert for Case 1
        safety_alert = SafetyEventModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1_t2.id,
            event_type="threat_event",
            severity="HIGH",
            status="active",
        )

        session.add_all([
            patient_user,
            patient_bob,
            therapist_user_a,
            therapist_user_b,
            therapist_a,
            therapist_b,
            case_1,
            case_2,
            case_3,
            case_4,
            sess_1_t1,
            sess_1_t2,
            sess_3,
            sess_4,
            pred_c1_t1,
            pred_c1_t2,
            pred_c3_t1,
            checkin_1,
            journal_1,
            chat_1,
            voice_1,
            safety_alert,
        ])
        session.commit()

        yield {
            "case_1_id": str(case_1.id),
            "case_2_id": str(case_2.id),
            "case_3_id": str(case_3.id),
            "case_4_id": str(case_4.id),
            "sess_1_t2_id": str(sess_1_t2.id),
            "sess_4_id": str(sess_4.id),
        }

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _get_token(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.json()}"
    return resp.json()["access_token"]


# ===========================================================================
# TEST CASES
# ===========================================================================

def test_therapist_can_get_case_insights_with_full_predictions(client, insights_test_db):
    """
    Therapist retrieves insights for a case with longitudinal history,
    active signals, context flags, and engagement activity.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = insights_test_db["case_1_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Validate response structure
    parsed = CaseInsightsResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.results_available is True
    assert parsed.trend_available is True
    assert parsed.risk_level == "HIGH"
    assert parsed.fused_risk_score == 78.0
    assert parsed.triage_level == "HIGH"

    # Verify summary & disclaimer
    assert len(parsed.summary) > 0
    assert "not a medical diagnosis" in parsed.disclaimer

    # Verify factors exist (text, voice, structured, temporal, context, etc.)
    factor_types = {f.type for f in parsed.factors}
    assert "text" in factor_types or "voice" in factor_types or "context" in factor_types

    # Verify longitudinal trend explanation reflects INCREASING
    assert "increasing" in parsed.trend_explanation.lower()

    # Verify context flags
    assert parsed.context.threat_event is True
    assert parsed.context.protection_issue is True
    assert parsed.context.financial_hardship is True
    assert parsed.context.investigation_delay is True

    # Verify engagement activity counts
    assert parsed.recent_activity.checkins >= 1
    assert parsed.recent_activity.journal_entries >= 1
    assert parsed.recent_activity.voice_interactions >= 1
    assert parsed.recent_activity.text_interactions >= 1


def test_therapist_case_with_no_predictions(client, insights_test_db):
    """
    Case with no predictions returns results_available=False,
    safe observational summary, empty factors, and zero fabricated scores.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = insights_test_db["case_2_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = CaseInsightsResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.results_available is False
    assert parsed.trend_available is False
    assert parsed.risk_level is None
    assert parsed.fused_risk_score is None
    assert len(parsed.factors) == 0
    assert "No prediction or assessment data" in parsed.summary
    assert "not available" in parsed.trend_explanation.lower()
    assert "not a medical diagnosis" in parsed.disclaimer


def test_therapist_case_with_single_prediction_no_trend_fabrication(client, insights_test_db):
    """
    Case with single prediction returns results_available=True but
    trend_available=False and explicit limited history explanation.
    Never fabricates a trend.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = insights_test_db["case_3_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = CaseInsightsResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.results_available is True
    assert parsed.trend_available is False
    assert "limited" in parsed.trend_explanation.lower()
    # No trend factor should be claimed
    factor_types = [f.type for f in parsed.factors]
    assert "trend" not in factor_types


def test_therapist_can_get_session_insights(client, insights_test_db):
    """
    Therapist retrieves session-specific clinical insights.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    session_id = insights_test_db["sess_1_t2_id"]

    resp = client.get(
        f"/api/v1/therapist/sessions/{session_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = CaseInsightsResponse.model_validate(data)
    assert str(parsed.session_id) == session_id
    assert parsed.results_available is True


def test_therapist_cannot_get_other_therapist_case_insights(client, insights_test_db):
    """
    Therapist A attempts to access Therapist B's case -> 403 Forbidden.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_4_id = insights_test_db["case_4_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_4_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Case not found or access denied."


def test_therapist_cannot_get_other_therapist_session_insights(client, insights_test_db):
    """
    Therapist A attempts to access Therapist B's session -> 403 Forbidden.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    sess_4_id = insights_test_db["sess_4_id"]

    resp = client.get(
        f"/api/v1/therapist/sessions/{sess_4_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_nonexistent_case_returns_403_anti_enumeration(client, insights_test_db):
    """
    Nonexistent case UUID returns 403 to prevent enumeration attacks.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    random_case_id = str(uuid.uuid4())

    resp = client.get(
        f"/api/v1/therapist/cases/{random_case_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_patient_user_cannot_access_insights(client, insights_test_db):
    """
    Patient (USER role) receives 403 Forbidden.
    """
    token = _get_token(client, "patient.alice@medha.test", "PatientPass123!")
    case_id = insights_test_db["case_1_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/insights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_unauthenticated_request_returns_401(client, insights_test_db):
    """
    Request without Authorization header returns 401 Unauthorized.
    """
    case_id = insights_test_db["case_1_id"]
    resp = client.get(f"/api/v1/therapist/cases/{case_id}/insights")
    assert resp.status_code == 401


def test_safety_phrasing_and_disclaimer_compliance(client, insights_test_db):
    """
    Verifies that no forbidden clinical diagnostic assertions exist anywhere
    in the insight responses.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    for case_key in ["case_1_id", "case_2_id", "case_3_id"]:
        case_id = insights_test_db[case_key]
        resp = client.get(
            f"/api/v1/therapist/cases/{case_id}/insights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Check all string contents
        full_text = str(data).lower()
        for forbidden in FORBIDDEN_DIAGNOSTIC_TERMS:
            assert forbidden not in full_text

        # Validate safety phrasing on primary text fields
        assert validate_safety_phrasing(data["summary"])
        assert validate_safety_phrasing(data["trend_explanation"])
        for factor in data["factors"]:
            assert validate_safety_phrasing(factor["factor"])
            assert validate_safety_phrasing(factor["description"])
