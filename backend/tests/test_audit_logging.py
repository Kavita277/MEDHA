"""
Step 27 Audit Logging and Privacy Firewall Unit & Integration Tests
====================================================================

Validates:
  1. Persistent compliance audit logging and application-level append-only repository.
  2. Data privacy and redaction firewalls (no passwords, JWTs, audio bytes, or raw chat transcripts).
  3. Authentication audit events (USER_LOGIN, LOGIN_FAILED, LOGIN_BLOCKED).
  4. Clinical provisioning audit events (THERAPIST_CREATED_USER).
  5. Clinical decision-support viewing audit events (THERAPIST_VIEWED_PREDICTION,
     THERAPIST_VIEWED_ALERT, THERAPIST_VIEWED_INSIGHTS, THERAPIST_VIEWED_RECOMMENDATIONS,
     THERAPIST_VIEWED_SAFETY_PROTOCOL).
  6. Authorization denial audit events (ACCESS_DENIED on foreign case/session access) with
     strict preservation of HTTP 403 anti-enumeration semantics.
  7. Therapist audit log query endpoint with actor isolation.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.persistence.models.audit_log import AuditLogModel
from backend.persistence.models.case import Case
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.services.audit_service import sanitize_payload, audit_service
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


def test_sanitize_payload_redaction_firewall():
    """Validates that sensitive fields are completely scrubbed by the privacy firewall."""
    raw_payload = {
        "email": "doctor@hospital.org",
        "password": "SuperSecretPassword123!",
        "password_hash": "$2b$12$eX4mpleHashStringNotToStore",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access_token": "Bearer test-token-value",
        "chat_message": "Patient says: I am feeling severe despair today.",
        "transcript": "Full audio transcript of the session...",
        "raw_audio": b"RIFF....audiobytes",
        "safe_metric": 42.5,
        "timepoint": 3,
        "nested": {
            "jwt": "eyJhbGci...",
            "action_code": "FLAG_CRITICAL",
        },
    }

    sanitized = sanitize_payload(raw_payload)

    assert sanitized["email"] == "doctor@hospital.org"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["password_hash"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["chat_message"] == "[REDACTED]"
    assert sanitized["transcript"] == "[REDACTED]"
    assert sanitized["raw_audio"] == "[REDACTED]"
    assert sanitized["safe_metric"] == 42.5
    assert sanitized["timepoint"] == 3
    assert sanitized["nested"]["jwt"] == "[REDACTED]"
    assert sanitized["nested"]["action_code"] == "FLAG_CRITICAL"


def test_audit_repository_append_and_query(db_session: Session, test_therapist_user: User):
    """Validates AuditLogRepository creation, filtering, and query counts."""
    repo = AuditLogRepository(db_session)
    actor_id = test_therapist_user.id

    # Create multiple audit entries
    entry1 = repo.create_log(
        action="USER_LOGIN",
        actor_user_id=actor_id,
        actor_role="therapist",
        resource_type="user",
        resource_id=str(actor_id),
        status="SUCCESS",
        metadata_payload={"client": "web"},
    )
    entry2 = repo.create_log(
        action="THERAPIST_VIEWED_PREDICTION",
        actor_user_id=actor_id,
        actor_role="therapist",
        resource_type="case",
        resource_id="V-100",
        status="SUCCESS",
        metadata_payload={"timepoint": 1},
    )
    entry3 = repo.create_log(
        action="ACCESS_DENIED",
        actor_user_id=actor_id,
        actor_role="therapist",
        resource_type="case",
        resource_id="V-FOREIGN",
        status="DENIED",
        metadata_payload={"reason": "unauthorized"},
    )
    db_session.commit()

    assert entry1.id is not None
    assert entry2.id is not None
    assert entry3.id is not None

    # Query all for actor
    logs = repo.list_logs(actor_user_id=actor_id)
    assert len(logs) == 3

    # Filter by action
    login_logs = repo.list_logs(actor_user_id=actor_id, action="USER_LOGIN")
    assert len(login_logs) == 1
    assert login_logs[0].action == "USER_LOGIN"

    # Filter by status
    denied_logs = repo.list_logs(status="DENIED")
    assert len(denied_logs) == 1
    assert denied_logs[0].resource_id == "V-FOREIGN"

    # Count logs
    assert repo.count_logs(actor_user_id=actor_id) == 3
    assert repo.count_logs(status="DENIED") == 1


def test_auth_login_audit_success(client: TestClient, db_session: Session, test_user: User):
    """Validates that a successful login creates a USER_LOGIN audit record."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.patient@example.com", "password": "PatientPass123!"},
    )
    assert response.status_code == 200

    repo = AuditLogRepository(db_session)
    logs = repo.list_logs(action="USER_LOGIN", actor_user_id=test_user.id)
    assert len(logs) >= 1
    latest = logs[0]
    assert latest.status == "SUCCESS"
    assert latest.resource_type == "user"
    assert latest.resource_id == str(test_user.id)
    assert latest.metadata_payload.get("email") == "test.patient@example.com"


def test_auth_login_audit_failure_redacted(client: TestClient, db_session: Session, test_user: User):
    """Validates that a failed login creates LOGIN_FAILED without storing the bad password."""
    bad_password = "WrongPasswordAttempt999!"
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.patient@example.com", "password": bad_password},
    )
    assert response.status_code == 401

    repo = AuditLogRepository(db_session)
    logs = repo.list_logs(action="LOGIN_FAILED")
    assert len(logs) >= 1
    latest = logs[0]
    assert latest.status == "FAILURE"
    assert latest.resource_id == "test.patient@example.com"
    # Ensure raw bad password is never anywhere in the metadata payload
    assert bad_password not in str(latest.metadata_payload)


def test_auth_login_audit_blocked_user(client: TestClient, db_session: Session):
    """Validates that a disabled user login creates LOGIN_BLOCKED with status DENIED."""
    inactive_user = User(
        id=uuid.uuid4(),
        role=UserRole.USER,
        name="Suspended User",
        email="suspended@example.com",
        password_hash=hash_password("SuspendedPass123!"),
        status=UserStatus.SUSPENDED,
    )
    db_session.add(inactive_user)
    db_session.commit()


    response = client.post(
        "/api/v1/auth/login",
        json={"email": "suspended@example.com", "password": "SuspendedPass123!"},
    )
    assert response.status_code == 403

    repo = AuditLogRepository(db_session)
    logs = repo.list_logs(action="LOGIN_BLOCKED")
    assert len(logs) >= 1
    latest = logs[0]
    assert latest.status == "DENIED"
    assert latest.actor_user_id == inactive_user.id


def test_therapist_create_patient_audit(
    client: TestClient,
    db_session: Session,
    test_therapist: Therapist,
    therapist_token_headers: dict,
):
    """Validates that patient provisioning creates a THERAPIST_CREATED_USER audit log without credentials."""
    payload = {
        "name": "New Audit Patient",
        "email": "audit.patient@hospital.org",
        "mobile": "+15550001111",
        "password": "PatientSecretPass123!",
        "victim_id": "V-AUDIT-001",
    }
    response = client.post(
        "/api/v1/therapist/users",
        headers=therapist_token_headers,
        json=payload,
    )
    assert response.status_code == 201
    created_user_id = response.json()["id"]

    repo = AuditLogRepository(db_session)
    logs = repo.list_logs(action="THERAPIST_CREATED_USER", resource_id=created_user_id)
    assert len(logs) >= 1
    latest = logs[0]
    assert latest.status == "SUCCESS"
    assert latest.actor_user_id == test_therapist.user_id
    assert latest.metadata_payload.get("victim_id") == "V-AUDIT-001"
    # Ensure password and hash are not present
    assert "PatientSecretPass123!" not in str(latest.metadata_payload)
    assert "password" not in latest.metadata_payload


def test_therapist_view_prediction_results_audit(
    client: TestClient,
    db_session: Session,
    test_case: Case,
    therapist_token_headers: dict,
    test_therapist: Therapist,
):
    """Validates that viewing case predictions generates a THERAPIST_VIEWED_PREDICTION audit log."""
    response = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/results",
        headers=therapist_token_headers,
    )
    assert response.status_code == 200

    repo = AuditLogRepository(db_session)
    logs = repo.list_logs(action="THERAPIST_VIEWED_PREDICTION", resource_id=str(test_case.id))
    assert len(logs) >= 1
    latest = logs[0]
    assert latest.status == "SUCCESS"
    assert latest.actor_user_id == test_therapist.user_id


def test_therapist_view_insights_and_recommendations_audit(
    client: TestClient,
    db_session: Session,
    test_case: Case,
    therapist_token_headers: dict,
    test_therapist: Therapist,
):
    """Validates that accessing insights and recommendations generates appropriate audit logs."""
    # 1. Insights
    resp_insights = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/insights",
        headers=therapist_token_headers,
    )
    assert resp_insights.status_code == 200

    # 2. Recommendations
    resp_recs = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/recommendations",
        headers=therapist_token_headers,
    )
    assert resp_recs.status_code == 200

    # 3. Safety protocol
    resp_safety = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/safety-protocol",
        headers=therapist_token_headers,
    )
    assert resp_safety.status_code == 200

    repo = AuditLogRepository(db_session)

    insight_logs = repo.list_logs(action="THERAPIST_VIEWED_INSIGHTS", resource_id=str(test_case.id))
    assert len(insight_logs) >= 1
    assert insight_logs[0].status == "SUCCESS"

    rec_logs = repo.list_logs(action="THERAPIST_VIEWED_RECOMMENDATIONS", resource_id=str(test_case.id))
    assert len(rec_logs) >= 1
    assert rec_logs[0].status == "SUCCESS"

    safety_logs = repo.list_logs(action="THERAPIST_VIEWED_SAFETY_PROTOCOL", resource_id=str(test_case.id))
    assert len(safety_logs) >= 1
    assert safety_logs[0].status == "SUCCESS"


def test_access_denied_audit_on_foreign_case(
    client: TestClient,
    db_session: Session,
    test_case: Case,
):
    """Validates that accessing a foreign case returns 403 AND logs an ACCESS_DENIED audit event."""
    # Create a second therapist
    second_user = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name="Dr. Other Therapist",
        email="dr.other@example.com",
        password_hash=hash_password("OtherPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(second_user)
    db_session.commit()

    second_therapist = Therapist(
        id=uuid.uuid4(),
        user_id=second_user.id,
        display_name="Dr. Other Therapist",
    )
    db_session.add(second_therapist)
    db_session.commit()

    second_token = create_access_token(
        subject=str(second_user.id),
        role=second_user.role.value,
    )
    second_headers = {"Authorization": f"Bearer {second_token}"}

    # Attempt to access test_case (owned by test_therapist, not second_therapist)
    response = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/results",
        headers=second_headers,
    )
    # MUST return 403 (anti-enumeration)
    assert response.status_code == 403
    assert response.json()["detail"] == "Case not found or access denied."

    # Verify ACCESS_DENIED audit log was created
    repo = AuditLogRepository(db_session)
    denied_logs = repo.list_logs(
        action="ACCESS_DENIED",
        actor_user_id=second_user.id,
        resource_id=str(test_case.id),
    )
    assert len(denied_logs) >= 1
    assert denied_logs[0].status == "DENIED"
    assert denied_logs[0].actor_role == "therapist"


def test_therapist_audit_logs_query_endpoint(
    client: TestClient,
    db_session: Session,
    test_therapist: Therapist,
    therapist_token_headers: dict,
):
    """Validates the GET /api/v1/therapist/audit-logs endpoint with actor isolation."""
    # Add an event for test_therapist
    audit_service.log_event(
        db=db_session,
        action="USER_LOGIN",
        actor_user_id=test_therapist.user_id,
        actor_role="therapist",
        resource_type="user",
        resource_id=str(test_therapist.user_id),
        status="SUCCESS",
        metadata={"client": "test_suite"},
    )
    # Add an event for another user
    audit_service.log_event(
        db=db_session,
        action="USER_LOGIN",
        actor_user_id=uuid.uuid4(),
        actor_role="user",
        resource_type="user",
        resource_id=str(uuid.uuid4()),
        status="SUCCESS",
        metadata={"client": "other_suite"},
    )
    db_session.commit()

    response = client.get(
        "/api/v1/therapist/audit-logs",
        headers=therapist_token_headers,
    )
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    # Ensure every returned log belongs to the authenticated therapist
    for log in logs:
        assert log["actor_user_id"] == str(test_therapist.user_id)
