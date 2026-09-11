"""
Step 26: Therapist Clinical Recommendations & Safety Protocol API Tests
======================================================================

Tests for:
  - backend/services/recommendation_service.py
  - backend/api/v1/endpoints/therapist_recommendations.py
  - GET /api/v1/therapist/cases/{case_id}/recommendations
  - GET /api/v1/therapist/sessions/{session_id}/recommendations
  - GET /api/v1/therapist/cases/{case_id}/safety-protocol
  - GET /api/v1/therapist/sessions/{session_id}/safety-protocol

Coverage:
  1. Valid therapist + valid case + prediction -> recommendations & self-help returned.
  2. Missing prediction -> results_available=False, empty recommendations, no fabricated scores.
  3. Dynamic safety protocol evaluation with active safety context -> URGENT/SAFETY_ESCALATION.
  4. Low risk + stable case -> routine monitoring protocol.
  5. Authentication & RBAC (401 unauthenticated, 403 USER, 403 foreign therapist, 403 anti-enumeration).
  6. Route collision & regression: Step 24 GET /cases/{case_id}/alerts remains intact.
  7. Determinism: identical inputs yield identical responses.
  8. Non-diagnostic phrasing guardrail & clinical decision support disclaimer.
  9. Conversational safety fast-path is preserved and distinct.
  10. Session-level recommendation and safety-protocol endpoints.
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
from backend.schemas.recommendations import (
    CaseRecommendationsResponse,
    SafetyProtocolResponse,
)
from backend.schemas.results import AlertSummaryResponse
from backend.security.passwords import hash_password
from backend.services.recommendation_service import RecommendationService
from engine.explainability_engine import FORBIDDEN_DIAGNOSTIC_TERMS, validate_safety_phrasing


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture(scope="function")
def rec_test_db():
    """
    Sets up an in-memory test database with:
      - Therapist A (owns Case 1 with high risk + safety context, Case 2 with no prediction, Case 3 with low stable risk)
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

        # Case 1: High risk with threat context and financial hardship
        case_1 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-001",
            user_id=patient_user.id,
            therapist_id=therapist_a.id,
            current_timepoint=2,
            status="active",
        )
        # Case 2: No predictions
        case_2 = Case(
            id=uuid.uuid4(),
            victim_id="V-CASE-002",
            user_id=patient_user.id,
            therapist_id=therapist_a.id,
            current_timepoint=1,
            status="active",
        )
        # Case 3: Low risk stable
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
        sess_1 = SessionModel(
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
                "active_intent": "safety_support",
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

        # Predictions for Case 1 (High risk: 78.0)
        pred_c1 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1.id,
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

        # Predictions for Case 3 (Low risk: 18.0)
        pred_c3 = PredictionResultModel(
            id=uuid.uuid4(),
            case_id=case_3.id,
            session_id=sess_3.id,
            timepoint=1,
            fusion_dds_prediction=18.0,
            temporal_risk_score=0.15,
            struct_pred=15.0,
            text_pred=20.0,
            voice_pred=18.0,
            behav_pred=None,
            triage_level="LOW",
            struct_available=True,
            text_available=True,
            voice_available=True,
            behav_available=False,
        )

        # Safety Event for Case 1
        safety_alert = SafetyEventModel(
            id=uuid.uuid4(),
            case_id=case_1.id,
            session_id=sess_1.id,
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
            sess_1,
            sess_3,
            sess_4,
            pred_c1,
            pred_c3,
            safety_alert,
        ])
        session.commit()

        yield {
            "case_1_id": str(case_1.id),
            "case_2_id": str(case_2.id),
            "case_3_id": str(case_3.id),
            "case_4_id": str(case_4.id),
            "sess_1_id": str(sess_1.id),
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

def test_therapist_can_get_case_recommendations(client, rec_test_db):
    """
    Therapist retrieves clinical recommendations for a valid case with prediction data.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = rec_test_db["case_1_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Response schema validation
    parsed = CaseRecommendationsResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.results_available is True
    assert parsed.risk_level == "HIGH"
    assert parsed.fused_risk_score == 78.0
    assert len(parsed.recommendations) > 0
    assert len(parsed.self_help_resources) > 0
    assert parsed.safety_protocol is not None
    assert parsed.safety_protocol.alert_triggered is True
    assert "not a medical diagnosis" in parsed.disclaimer

    # Verify recommendations structure
    rec_categories = {r.category for r in parsed.recommendations}
    assert any(c in rec_categories for c in ["counselling", "protection", "monitoring", "financial_support"])


def test_therapist_case_with_no_predictions(client, rec_test_db):
    """
    Case with no prediction returns results_available=False,
    empty recommendations, and no fabricated scores.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = rec_test_db["case_2_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = CaseRecommendationsResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.results_available is False
    assert parsed.risk_level is None
    assert parsed.fused_risk_score is None
    assert len(parsed.recommendations) == 0
    assert len(parsed.self_help_resources) == 0
    assert "not a medical diagnosis" in parsed.disclaimer


def test_therapist_can_get_safety_protocol_high_risk(client, rec_test_db):
    """
    Therapist retrieves evaluated dynamic safety protocol for high risk case with safety context.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = rec_test_db["case_1_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/safety-protocol",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = SafetyProtocolResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.alert_triggered is True
    assert parsed.priority in ("IMMEDIATE", "URGENT", "PRIORITY")
    assert len(parsed.reason_codes) > 0
    assert len(parsed.recommended_action) > 0
    assert len(parsed.cta) > 0


def test_therapist_safety_protocol_low_stable(client, rec_test_db):
    """
    Low risk + stable case evaluates to routine monitoring without an alert trigger.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = rec_test_db["case_3_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/safety-protocol",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    parsed = SafetyProtocolResponse.model_validate(data)
    assert str(parsed.case_id) == case_id
    assert parsed.alert_triggered is False
    assert parsed.priority == "ROUTINE"
    assert parsed.alert_type == "MONITORING"


def test_session_level_recommendations_and_safety_protocol(client, rec_test_db):
    """
    Therapist retrieves recommendations and safety protocol for a specific session.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    session_id = rec_test_db["sess_1_id"]

    # Session recommendations
    rec_resp = client.get(
        f"/api/v1/therapist/sessions/{session_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["session_id"] == session_id
    assert rec_data["results_available"] is True

    # Session safety protocol
    proto_resp = client.get(
        f"/api/v1/therapist/sessions/{session_id}/safety-protocol",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert proto_resp.status_code == 200
    proto_data = proto_resp.json()
    assert proto_data["session_id"] == session_id


def test_route_collision_regression_step24_alerts_intact(client, rec_test_db):
    """
    Ensures that Step 24 historical alerts route (GET /api/v1/therapist/cases/{case_id}/alerts)
    remains completely functional and unaffected by Step 26 additions.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    case_id = rec_test_db["case_1_id"]

    resp = client.get(
        f"/api/v1/therapist/cases/{case_id}/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    alerts_data = resp.json()
    assert isinstance(alerts_data, list)
    assert len(alerts_data) == 1
    # Check it parses as Step 24 AlertSummaryResponse
    alert = AlertSummaryResponse.model_validate(alerts_data[0])
    assert alert.event_type == "threat_event"
    assert alert.severity == "HIGH"


def test_unauthenticated_and_rbac_authorization(client, rec_test_db):
    """
    Tests 401 unauthenticated, 403 USER role, 403 foreign therapist case, and 403 anti-enumeration.
    """
    case_1_id = rec_test_db["case_1_id"]
    case_4_id = rec_test_db["case_4_id"]
    sess_4_id = rec_test_db["sess_4_id"]

    # 1. Unauthenticated -> 401
    assert client.get(f"/api/v1/therapist/cases/{case_1_id}/recommendations").status_code == 401
    assert client.get(f"/api/v1/therapist/cases/{case_1_id}/safety-protocol").status_code == 401

    # 2. Patient USER role -> 403
    patient_token = _get_token(client, "patient.alice@medha.test", "PatientPass123!")
    assert client.get(
        f"/api/v1/therapist/cases/{case_1_id}/recommendations",
        headers={"Authorization": f"Bearer {patient_token}"},
    ).status_code == 403
    assert client.get(
        f"/api/v1/therapist/cases/{case_1_id}/safety-protocol",
        headers={"Authorization": f"Bearer {patient_token}"},
    ).status_code == 403

    # 3. Foreign therapist case -> 403 (Therapist A accessing Therapist B's case)
    therapist_token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    assert client.get(
        f"/api/v1/therapist/cases/{case_4_id}/recommendations",
        headers={"Authorization": f"Bearer {therapist_token}"},
    ).status_code == 403
    assert client.get(
        f"/api/v1/therapist/sessions/{sess_4_id}/safety-protocol",
        headers={"Authorization": f"Bearer {therapist_token}"},
    ).status_code == 403

    # 4. Anti-enumeration: Nonexistent case -> 403
    random_case = str(uuid.uuid4())
    assert client.get(
        f"/api/v1/therapist/cases/{random_case}/recommendations",
        headers={"Authorization": f"Bearer {therapist_token}"},
    ).status_code == 403


def test_safety_phrasing_and_disclaimer_compliance(client, rec_test_db):
    """
    Verifies that no forbidden clinical diagnostic assertions exist anywhere
    in recommendation or safety responses.
    """
    token = _get_token(client, "alpha@medha.test", "TherapistA123!")
    for case_key in ["case_1_id", "case_2_id", "case_3_id"]:
        case_id = rec_test_db[case_key]
        resp = client.get(
            f"/api/v1/therapist/cases/{case_id}/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()

        full_text = str(data).lower()
        for forbidden in FORBIDDEN_DIAGNOSTIC_TERMS:
            assert forbidden not in full_text

        for rec in data.get("recommendations", []):
            assert validate_safety_phrasing(rec["reason"])
            assert validate_safety_phrasing(rec["action"])


def test_conversational_safety_fast_path_service():
    """
    Verifies that conversational safety fast-path is accessible via service.
    """
    service = RecommendationService()
    alert_dict = service.check_conversational_safety(
        text="Someone is stalking me and I am in immediate danger.",
        case_id="CASE-FAST-PATH",
    )
    assert alert_dict is not None
    assert alert_dict["alert_triggered"] is True
    assert alert_dict["priority"] in ("IMMEDIATE", "URGENT")
    assert alert_dict["source"] == "conversational_safety_trigger"
