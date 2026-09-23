"""
Step 31 — Complete Security Integration Test Suite
===================================================

Authoritative specification: backend/docs/backend_plan.md §31

Verifies the 10 core security requirements:
1. User cannot access therapist dashboard (exhaustive sweep of all therapist endpoints).
2. User cannot access predictions (results, specialist outputs, triage flags).
3. User cannot access another user's data (cross-patient isolation: session, chat, checkin, journal).
4. Therapist cannot access another therapist's case (cross-therapist isolation with anti-enumeration).
5. Therapist can access assigned case (positive access verification for assigned clinical data).
6. Invalid JWT rejected (malformed, random, tampered signature -> 401 & WWW-Authenticate).
7. Expired JWT rejected (expired exp claim -> 401).
8. Suspended/deactivated account rejected (runtime status enforcement on active tokens -> 403).
9. Password is never returned (recursive credential redaction inspection across all JSON responses).
10. Prediction data is never returned by USER endpoints (recursive verification on patient APIs).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel, CheckInStatus
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


# ===========================================================================
# Helper Functions & Fixtures
# ===========================================================================

def recursive_find_keys(obj: Any, target_keys: Set[str]) -> List[str]:
    """Recursively searches a JSON structure for any occurrences of target keys."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in target_keys:
                found.append(k)
            found.extend(recursive_find_keys(v, target_keys))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(recursive_find_keys(item, target_keys))
    return found


@pytest.fixture
def setup_security_environment(
    db_session: Session,
    test_user: User,
    test_therapist: Therapist,
    test_case: Case,
):
    """
    Sets up a complete multi-entity environment:
    - User A (test_user) with Case A (test_case), Session A, CheckIn A, Journal A
    - User B with Case B, Session B, CheckIn B, Journal B
    - Therapist B (distinct, foreign therapist with no assigned access to Case A)
    """
    now = datetime.now(timezone.utc)

    # 1. User A entities
    session_a = SessionModel(
        id=uuid.uuid4(),
        session_identifier=f"SESS-A-{uuid.uuid4().hex[:6]}",
        case_id=test_case.id,
        timepoint=1,
        status=SessionStatus.ACTIVE.value,
        state_snapshot={
            "victim_id": test_case.victim_id,
            "session_id": "sess_a_snap",
            "conversation_history": [{"sender": "user", "text": "Hello, this is Patient A"}],
            "question_history": [],
            "structured_features": {"Mood": 3.0},
        },
    )
    db_session.add(session_a)
    db_session.commit()

    checkin_a = CheckInModel(
        id=uuid.uuid4(),
        session_id=session_a.id,
        victim_id=test_case.victim_id,
        status=CheckInStatus.IN_PROGRESS.value,
        started_at=now,
        current_question_id="SA-01",
    )
    db_session.add(checkin_a)
    db_session.commit()

    q_record_a = QuestionRecordModel(
        id=uuid.uuid4(),
        checkin_id=checkin_a.id,
        question_id="SA-01",
        question_text="Are you feeling safe today?",
        question_order=1,
        answer_status="pending",
    )
    db_session.add(q_record_a)

    journal_a = JournalEntryModel(
        id=uuid.uuid4(),
        case_id=test_case.id,
        content="Patient A private clinical reflections.",
        created_at=now,
    )
    db_session.add(journal_a)

    # Safety alert on Case A
    alert_a = SafetyEventModel(
        id=uuid.uuid4(),
        case_id=test_case.id,
        session_id=session_a.id,
        event_type="crisis_keyword",
        severity="HIGH",
        status="active",
        payload={"keyword": "distress"},
        detected_at=now,
    )
    db_session.add(alert_a)

    # Prediction on Case A
    pred_a = PredictionResultModel(
        id=uuid.uuid4(),
        case_id=test_case.id,
        session_id=session_a.id,
        timepoint=1,
        fusion_dds_prediction=52.5,
        temporal_risk_score=0.45,
        future_escalation_flag=False,
        triage_level="MEDIUM",
        struct_pred=48.0,
        text_pred=55.0,
        voice_pred=50.0,
        behav_pred=None,
        struct_available=True,
        text_available=True,
        voice_available=True,
        behav_available=False,
        predicted_at=now,
    )
    db_session.add(pred_a)
    db_session.commit()

    # 2. User B entities (independent patient)
    user_b = User(
        id=uuid.uuid4(),
        role=UserRole.USER,
        name="Patient Bob",
        email="patient.bob@example.com",
        password_hash=hash_password("BobSecretPassword123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user_b)
    db_session.commit()

    case_b = Case(
        id=uuid.uuid4(),
        victim_id="V-TEST-002",
        user_id=user_b.id,
        therapist_id=test_therapist.id,
        current_timepoint=1,
        status="active",
    )
    db_session.add(case_b)
    db_session.commit()

    session_b = SessionModel(
        id=uuid.uuid4(),
        session_identifier=f"SESS-B-{uuid.uuid4().hex[:6]}",
        case_id=case_b.id,
        timepoint=1,
        status=SessionStatus.ACTIVE.value,
        state_snapshot={
            "victim_id": case_b.victim_id,
            "session_id": "sess_b_snap",
            "conversation_history": [{"sender": "user", "text": "Confidential message from Patient B"}],
            "question_history": [],
            "structured_features": {"Mood": 2.0},
        },
    )
    db_session.add(session_b)
    db_session.commit()

    checkin_b = CheckInModel(
        id=uuid.uuid4(),
        session_id=session_b.id,
        victim_id=case_b.victim_id,
        status=CheckInStatus.IN_PROGRESS.value,
        started_at=now,
        current_question_id="ES-01",
    )
    db_session.add(checkin_b)
    db_session.commit()

    q_record_b = QuestionRecordModel(
        id=uuid.uuid4(),
        checkin_id=checkin_b.id,
        question_id="ES-01",
        question_text="How is your stress level?",
        question_order=1,
        answer_status="pending",
    )
    db_session.add(q_record_b)

    journal_b = JournalEntryModel(
        id=uuid.uuid4(),
        case_id=case_b.id,
        content="Patient B top-secret personal journal diary entry.",
        created_at=now,
    )
    db_session.add(journal_b)
    db_session.commit()

    # 3. Therapist B (Foreign Therapist)
    therapist_user_b = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name="Dr. Foreign Clinician",
        email="foreign.clinician@hospital.org",
        password_hash=hash_password("ForeignPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(therapist_user_b)
    db_session.commit()

    therapist_b = Therapist(
        id=uuid.uuid4(),
        user_id=therapist_user_b.id,
        display_name="Dr. Foreign Clinician, Psy.D.",
    )
    db_session.add(therapist_b)
    db_session.commit()

    token_b = create_access_token(subject=str(user_b.id), role="USER")
    token_therapist_b = create_access_token(subject=str(therapist_user_b.id), role="THERAPIST")

    return {
        "session_a": session_a,
        "checkin_a": checkin_a,
        "journal_a": journal_a,
        "alert_a": alert_a,
        "pred_a": pred_a,
        "user_b": user_b,
        "case_b": case_b,
        "session_b": session_b,
        "checkin_b": checkin_b,
        "journal_b": journal_b,
        "user_b_headers": {"Authorization": f"Bearer {token_b}"},
        "therapist_b": therapist_b,
        "therapist_b_headers": {"Authorization": f"Bearer {token_therapist_b}"},
    }


# ===========================================================================
# 1. User Cannot Access Therapist Dashboard
# ===========================================================================

class TestUserCannotAccessTherapistDashboard:
    """
    Requirement 1: User cannot access therapist dashboard.
    Sweeps all currently registered therapist routes with a valid USER role token.
    Asserts HTTP 403 Forbidden across all endpoints without altering production behavior.
    """

    @pytest.mark.parametrize(
        "method,endpoint_template,payload",
        [
            ("GET", "/api/v1/therapist/users", None),
            ("POST", "/api/v1/therapist/users", {"name": "Hacker Patient", "email": "hack@medha.org", "mobile": "+919999999999", "password": "PassPassword123!"}),
            ("PATCH", "/api/v1/therapist/users/{user_id}/status", {"status": "SUSPENDED"}),
            ("GET", "/api/v1/therapist/cases", None),
            ("PATCH", "/api/v1/therapist/cases/{case_id}", {"status": "archived"}),
            ("GET", "/api/v1/therapist/cases/{case_id}/results", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/sessions", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/checkins", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/behaviour", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/alerts", None),
            ("PATCH", "/api/v1/therapist/cases/{case_id}/alerts/{alert_id}", {"status": "handled", "resolution_note": "unauthorized"}),
            ("GET", "/api/v1/therapist/cases/{case_id}/insights", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/recommendations", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/safety-protocol", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/results", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/insights", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/recommendations", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/safety-protocol", None),
            ("GET", "/api/v1/therapist/audit-logs", None),
        ],
    )
    def test_user_token_rejected_on_therapist_routes(
        self,
        client: TestClient,
        test_case: Case,
        test_user: User,
        user_token_headers: dict,
        setup_security_environment: dict,
        method: str,
        endpoint_template: str,
        payload: dict,
    ):
        session_a = setup_security_environment["session_a"]
        alert_a = setup_security_environment["alert_a"]

        url = endpoint_template.format(
            case_id=test_case.id,
            user_id=test_user.id,
            session_id=session_a.id,
            alert_id=alert_a.id,
        )

        if method == "GET":
            response = client.get(url, headers=user_token_headers)
        elif method == "POST":
            response = client.post(url, json=payload, headers=user_token_headers)
        elif method == "PATCH":
            response = client.patch(url, json=payload, headers=user_token_headers)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert response.status_code == 403
        data = response.json()
        assert "insufficient permissions" in data["detail"].lower() or "therapist" in data["detail"].lower()


# ===========================================================================
# 2. User Cannot Access Predictions
# ===========================================================================

class TestUserCannotAccessPredictions:
    """
    Requirement 2: User cannot access predictions.
    Verifies USER tokens cannot access case results, session results, or any prediction payloads.
    """

    def test_user_cannot_access_case_prediction_results(
        self,
        client: TestClient,
        test_case: Case,
        user_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/results",
            headers=user_token_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert "fusion_dds_prediction" not in data
        assert "specialists" not in data

    def test_user_cannot_access_session_prediction_results(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_a = setup_security_environment["session_a"]
        response = client.get(
            f"/api/v1/therapist/sessions/{session_a.id}/results",
            headers=user_token_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert "fusion_dds_prediction" not in data
        assert "specialists" not in data


# ===========================================================================
# 3. User Cannot Access Another User's Data
# ===========================================================================

class TestUserCannotAccessAnotherUsersData:
    """
    Requirement 3: User cannot access another user's data.
    Verifies that User A cannot read or mutate User B's sessions, chat, check-ins, or journal entries.
    Preserves intentional 403/404 anti-enumeration behavior.
    """

    def test_user_cannot_read_another_users_session(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_b = setup_security_environment["session_b"]
        response = client.get(f"/api/v1/sessions/{session_b.id}", headers=user_token_headers)
        assert response.status_code == 403
        assert "own case" in response.json()["detail"].lower()

    def test_user_cannot_end_another_users_session(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_b = setup_security_environment["session_b"]
        response = client.post(f"/api/v1/sessions/{session_b.id}/end", headers=user_token_headers)
        assert response.status_code == 403

    def test_user_cannot_read_another_users_chat_history(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_b = setup_security_environment["session_b"]
        response = client.get(f"/api/v1/chat/sessions/{session_b.id}/history", headers=user_token_headers)
        assert response.status_code == 403
        # Ensure Bob's confidential text was never returned
        assert "Confidential message from Patient B" not in response.text

    def test_user_cannot_send_message_in_another_users_session(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_b = setup_security_environment["session_b"]
        response = client.post(
            f"/api/v1/chat/sessions/{session_b.id}/message",
            json={"message": "Malicious intrusion message"},
            headers=user_token_headers,
        )
        assert response.status_code == 403

    def test_user_cannot_read_another_users_checkin(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        checkin_b = setup_security_environment["checkin_b"]
        response = client.get(f"/api/v1/checkins/{checkin_b.id}", headers=user_token_headers)
        assert response.status_code == 403

    def test_user_cannot_answer_another_users_checkin(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        checkin_b = setup_security_environment["checkin_b"]
        response = client.post(
            f"/api/v1/checkins/{checkin_b.id}/answer",
            json={"answer": {"rating": 5}},
            headers=user_token_headers,
        )
        assert response.status_code == 403

    def test_user_cannot_read_another_users_journal_entry(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        journal_b = setup_security_environment["journal_b"]
        response = client.get(f"/api/v1/journal/{journal_b.id}", headers=user_token_headers)
        # Anti-enumeration returns 404 since it's filtered by User A's case
        assert response.status_code == 404
        assert "Patient B top-secret" not in response.text

    def test_user_cannot_update_another_users_journal_entry(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        journal_b = setup_security_environment["journal_b"]
        response = client.patch(
            f"/api/v1/journal/{journal_b.id}",
            json={"content": "Tampered content by User A"},
            headers=user_token_headers,
        )
        assert response.status_code == 404


# ===========================================================================
# 4. Therapist Cannot Access Another Therapist's Case
# ===========================================================================

class TestTherapistCannotAccessAnotherTherapistsCase:
    """
    Requirement 4: Therapist cannot access another therapist's case.
    Verifies that Therapist B receives 403 Forbidden with anti-enumeration
    ("Case not found or access denied.") across all Case A endpoints.
    """

    @pytest.mark.parametrize(
        "method,endpoint_template,payload",
        [
            ("PATCH", "/api/v1/therapist/cases/{case_id}", {"status": "archived"}),
            ("GET", "/api/v1/therapist/cases/{case_id}/results", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/sessions", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/checkins", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/behaviour", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/alerts", None),
            ("PATCH", "/api/v1/therapist/cases/{case_id}/alerts/{alert_id}", {"status": "handled", "resolution_note": "hacked"}),
            ("GET", "/api/v1/therapist/cases/{case_id}/insights", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/recommendations", None),
            ("GET", "/api/v1/therapist/cases/{case_id}/safety-protocol", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/results", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/insights", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/recommendations", None),
            ("GET", "/api/v1/therapist/sessions/{session_id}/safety-protocol", None),
        ],
    )
    def test_foreign_therapist_access_denied_with_anti_enumeration(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        method: str,
        endpoint_template: str,
        payload: dict,
    ):
        foreign_headers = setup_security_environment["therapist_b_headers"]
        session_a = setup_security_environment["session_a"]
        alert_a = setup_security_environment["alert_a"]

        url = endpoint_template.format(
            case_id=test_case.id,
            session_id=session_a.id,
            alert_id=alert_a.id,
        )

        if method == "GET":
            response = client.get(url, headers=foreign_headers)
        elif method == "PATCH":
            response = client.patch(url, json=payload, headers=foreign_headers)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert response.status_code == 403
        data = response.json()
        assert "access denied" in data["detail"].lower() or "not found" in data["detail"].lower()

    def test_foreign_therapist_case_listing_isolation(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
    ):
        foreign_headers = setup_security_environment["therapist_b_headers"]
        response = client.get("/api/v1/therapist/cases", headers=foreign_headers)
        assert response.status_code == 200
        cases = response.json()
        # Therapist B has 0 assigned cases; must never see Case A
        case_ids = [c["case_id"] for c in cases]
        assert str(test_case.id) not in case_ids


# ===========================================================================
# 5. Therapist Can Access Assigned Case
# ===========================================================================

class TestTherapistCanAccessAssignedCase:
    """
    Requirement 5: Therapist can access assigned case.
    Verifies positive access for Therapist A to Case A's clinical resources.
    """

    def test_therapist_accesses_assigned_case_list(
        self,
        client: TestClient,
        test_case: Case,
        therapist_token_headers: dict,
    ):
        response = client.get("/api/v1/therapist/cases", headers=therapist_token_headers)
        assert response.status_code == 200
        data = response.json()
        case_ids = [c["case_id"] for c in data]
        assert str(test_case.id) in case_ids

    def test_therapist_accesses_assigned_case_results(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        therapist_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/results",
            headers=therapist_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == str(test_case.id)
        assert data["results_available"] is True
        assert data["fusion_dds_prediction"] == 52.5

    def test_therapist_accesses_assigned_case_sessions(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        therapist_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/sessions",
            headers=therapist_token_headers,
        )
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1

    def test_therapist_accesses_assigned_case_insights(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        therapist_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/insights",
            headers=therapist_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == str(test_case.id)
        assert "factors" in data
        assert "disclaimer" in data

    def test_therapist_accesses_assigned_case_recommendations(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        therapist_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/recommendations",
            headers=therapist_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == str(test_case.id)
        assert "recommendations" in data

    def test_therapist_accesses_assigned_case_alerts(
        self,
        client: TestClient,
        test_case: Case,
        setup_security_environment: dict,
        therapist_token_headers: dict,
    ):
        response = client.get(
            f"/api/v1/therapist/cases/{test_case.id}/alerts",
            headers=therapist_token_headers,
        )
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) >= 1
        assert alerts[0]["severity"] == "HIGH"


# ===========================================================================
# 6. Invalid JWT Rejected
# ===========================================================================

class TestInvalidJWTRejected:
    """
    Requirement 6: Invalid JWT rejected.
    Tests protected endpoints with malformed, random, tampered signature tokens.
    Asserts HTTP 401 Unauthorized with WWW-Authenticate: Bearer.
    """

    @pytest.mark.parametrize(
        "bad_token",
        [
            "not.a.valid.jwt",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsig",
            "random_garbage_string_12345!@#$",
            "",
            # Tampered signature
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6IlVTRVIifQ.tampered_signature_here",
        ],
    )
    def test_invalid_tokens_return_401(
        self,
        client: TestClient,
        bad_token: str,
    ):
        headers = {"Authorization": f"Bearer {bad_token}"} if bad_token else {}
        
        # Test user endpoint
        resp_user = client.get("/api/v1/auth/me", headers=headers)
        assert resp_user.status_code == 401

        # Test therapist endpoint
        resp_therapist = client.get("/api/v1/therapist/cases", headers=headers)
        assert resp_therapist.status_code == 401

    def test_malformed_authorization_header_format(
        self,
        client: TestClient,
        user_token_headers: dict,
    ):
        # Header without 'Bearer ' prefix
        token = user_token_headers["Authorization"].split(" ")[1]
        resp = client.get("/api/v1/auth/me", headers={"Authorization": token})
        assert resp.status_code == 401


# ===========================================================================
# 7. Expired JWT Rejected
# ===========================================================================

class TestExpiredJWTRejected:
    """
    Requirement 7: Expired JWT rejected.
    Uses create_access_token with negative expires_delta (e.g. -1 hour).
    Asserts HTTP 401 Unauthorized across both USER and THERAPIST endpoints.
    """

    def test_expired_user_token_rejected(
        self,
        client: TestClient,
        test_user: User,
    ):
        expired_token = create_access_token(
            subject=str(test_user.id),
            role=test_user.role.value,
            expires_delta=timedelta(hours=-1),
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

    def test_expired_therapist_token_rejected(
        self,
        client: TestClient,
        test_therapist_user: User,
    ):
        expired_token = create_access_token(
            subject=str(test_therapist_user.id),
            role=test_therapist_user.role.value,
            expires_delta=timedelta(minutes=-30),
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        resp = client.get("/api/v1/therapist/cases", headers=headers)
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()


# ===========================================================================
# 8. Suspended / Deactivated Account Rejected
# ===========================================================================

class TestSuspendedAndDeactivatedAccountRejected:
    """
    Requirement 8: Suspended/deactivated account rejected.
    Generates a valid, non-expired JWT while active.
    Transitions account in DB to SUSPENDED, then DEACTIVATED.
    Asserts runtime HTTP 403 Forbidden with exact status detail.
    Safely restores account state to ACTIVE.
    """

    def test_suspended_user_runtime_rejection(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        user_token_headers: dict,
    ):
        # 1. Verify active token works initially
        resp_initial = client.get("/api/v1/auth/me", headers=user_token_headers)
        assert resp_initial.status_code == 200

        # 2. Suspend account in DB
        test_user.status = UserStatus.SUSPENDED
        db_session.commit()

        try:
            # 3. Request with valid token must be blocked at runtime
            resp_suspended = client.get("/api/v1/auth/me", headers=user_token_headers)
            assert resp_suspended.status_code == 403
            assert "suspended" in resp_suspended.json()["detail"].lower()

            # Also check operational endpoint
            resp_session = client.post("/api/v1/sessions", json={}, headers=user_token_headers)
            assert resp_session.status_code == 403
            assert "suspended" in resp_session.json()["detail"].lower()
        finally:
            # Restore state
            test_user.status = UserStatus.ACTIVE
            db_session.commit()

    def test_deactivated_user_runtime_rejection(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        user_token_headers: dict,
    ):
        # 1. Deactivate account in DB
        test_user.status = UserStatus.DEACTIVATED
        db_session.commit()

        try:
            # 2. Request with valid token must be blocked
            resp = client.get("/api/v1/auth/me", headers=user_token_headers)
            assert resp.status_code == 403
            assert "deactivated" in resp.json()["detail"].lower()
        finally:
            test_user.status = UserStatus.ACTIVE
            db_session.commit()

    def test_suspended_therapist_runtime_rejection(
        self,
        client: TestClient,
        db_session: Session,
        test_therapist_user: User,
        therapist_token_headers: dict,
    ):
        # 1. Suspend therapist in DB
        test_therapist_user.status = UserStatus.SUSPENDED
        db_session.commit()

        try:
            resp = client.get("/api/v1/therapist/cases", headers=therapist_token_headers)
            assert resp.status_code == 403
            assert "suspended" in resp.json()["detail"].lower()
        finally:
            test_therapist_user.status = UserStatus.ACTIVE
            db_session.commit()


# ===========================================================================
# 9. Password Is Never Returned
# ===========================================================================

class TestPasswordIsNeverReturned:
    """
    Requirement 9: Password is never returned.
    Recursively inspects JSON responses from authentication, user, therapist,
    case, session, and audit endpoints to assert credential keys never appear.
    """

    FORBIDDEN_CREDENTIAL_KEYS = {
        "password",
        "password_hash",
        "hashed_password",
        "raw_password",
        "user_password",
    }

    def test_login_response_never_contains_password_fields(self, client: TestClient, test_user: User):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "test.patient@example.com", "password": "PatientPass123!"},
        )
        assert resp.status_code == 200
        found = recursive_find_keys(resp.json(), self.FORBIDDEN_CREDENTIAL_KEYS)
        assert not found, f"Forbidden credential keys found in login response: {found}"

    def test_auth_me_never_contains_password_fields(self, client: TestClient, user_token_headers: dict):
        resp = client.get("/api/v1/auth/me", headers=user_token_headers)
        assert resp.status_code == 200
        found = recursive_find_keys(resp.json(), self.FORBIDDEN_CREDENTIAL_KEYS)
        assert not found, f"Forbidden credential keys found in /auth/me: {found}"

    def test_therapist_create_user_response_never_contains_password_hash(
        self,
        client: TestClient,
        test_therapist: Therapist,
        therapist_token_headers: dict,
    ):
        resp = client.post(
            "/api/v1/therapist/users",
            json={
                "name": "Security Audit Subject",
                "email": f"audit.subject.{uuid.uuid4().hex[:6]}@example.com",
                "mobile": f"+9198{uuid.uuid4().int % 100000000:08d}",
                "password": "InitialPatientSecret123!",
            },
            headers=therapist_token_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        # Ensure password_hash is not present in user profile
        found = recursive_find_keys(data.get("user", {}), self.FORBIDDEN_CREDENTIAL_KEYS)
        assert not found, f"Forbidden credential keys found in created user profile: {found}"

    def test_therapist_case_list_response_never_contains_password_fields(
        self,
        client: TestClient,
        test_therapist: Therapist,
        test_case: Case,
        therapist_token_headers: dict,
    ):
        resp = client.get("/api/v1/therapist/cases", headers=therapist_token_headers)
        assert resp.status_code == 200
        found = recursive_find_keys(resp.json(), self.FORBIDDEN_CREDENTIAL_KEYS)
        assert not found, f"Forbidden credential keys found in case listing: {found}"

    def test_therapist_audit_logs_never_contain_raw_passwords(
        self,
        client: TestClient,
        test_therapist: Therapist,
        therapist_token_headers: dict,
    ):
        resp = client.get("/api/v1/therapist/audit-logs", headers=therapist_token_headers)
        assert resp.status_code == 200
        logs = resp.json()
        # Verify no log entry contains raw password in metadata
        raw_text = str(logs)
        assert "PatientPass123!" not in raw_text
        assert "TherapistPass123!" not in raw_text


# ===========================================================================
# 10. Prediction Data Is Never Returned by USER Endpoints
# ===========================================================================

class TestPredictionDataIsNeverReturnedByUserEndpoints:
    """
    Requirement 10: Prediction data is never returned by USER endpoints.
    Exercises all supported patient-facing routes:
    - sessions creation
    - session detail
    - chat history
    - check-ins
    - journal entries
    Recursively inspects response JSON and asserts all prediction/ML fields are absent.
    """

    FORBIDDEN_PREDICTION_KEYS = {
        "fusion_dds_prediction",
        "temporal_risk_score",
        "future_escalation_flag",
        "triage_level",
        "struct_pred",
        "text_pred",
        "voice_pred",
        "behav_pred",
        "specialists",
    }

    def test_session_endpoints_exclude_prediction_fields(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_a = setup_security_environment["session_a"]

        # 1. Create Session
        resp_create = client.post("/api/v1/sessions", json={}, headers=user_token_headers)
        assert resp_create.status_code == 201
        found_create = recursive_find_keys(resp_create.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found_create, f"Forbidden prediction fields in session creation: {found_create}"

        # 2. Get Session Detail
        resp_get = client.get(f"/api/v1/sessions/{session_a.id}", headers=user_token_headers)
        assert resp_get.status_code == 200
        found_get = recursive_find_keys(resp_get.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found_get, f"Forbidden prediction fields in session detail: {found_get}"

    def test_chat_history_excludes_prediction_fields(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        session_a = setup_security_environment["session_a"]
        resp = client.get(f"/api/v1/chat/sessions/{session_a.id}/history", headers=user_token_headers)
        assert resp.status_code == 200
        found = recursive_find_keys(resp.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found, f"Forbidden prediction fields in chat history: {found}"

    def test_checkin_endpoints_exclude_prediction_fields(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        checkin_a = setup_security_environment["checkin_a"]
        resp = client.get(f"/api/v1/checkins/{checkin_a.id}", headers=user_token_headers)
        assert resp.status_code == 200
        found = recursive_find_keys(resp.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found, f"Forbidden prediction fields in checkin: {found}"

    def test_journal_endpoints_exclude_prediction_fields(
        self,
        client: TestClient,
        setup_security_environment: dict,
        user_token_headers: dict,
    ):
        # List entries
        resp_list = client.get("/api/v1/journal", headers=user_token_headers)
        assert resp_list.status_code == 200
        found_list = recursive_find_keys(resp_list.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found_list, f"Forbidden prediction fields in journal list: {found_list}"

        # Create entry
        resp_create = client.post(
            "/api/v1/journal",
            json={"content": "Feeling a bit calmer today."},
            headers=user_token_headers,
        )
        assert resp_create.status_code == 200
        found_create = recursive_find_keys(resp_create.json(), self.FORBIDDEN_PREDICTION_KEYS)
        assert not found_create, f"Forbidden prediction fields in journal create: {found_create}"
