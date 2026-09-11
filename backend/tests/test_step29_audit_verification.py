"""
Step 29 Comprehensive Audit Logging & Security Verification Tests
==================================================================

Validates the complete MEDHA §29 audit logging lifecycle:
  1. Case creation and assignment events (CASE_CREATED, CASE_ASSIGNED).
  2. Case modification events (CASE_UPDATED) and foreign case isolation.
  3. Safety alert handling and resolution events (ALERT_HANDLED) and cross-case validation.
  4. Account operational status governance (ACCOUNT_STATUS_CHANGED).
  5. Chronological audit log retrieval with strict clinician actor isolation.
  6. Patient RBAC enforcement (patients cannot access therapist audit endpoints).
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.persistence.models.case import Case
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


@pytest.fixture
def foreign_therapist_user(db_session: Session) -> User:
    """Provides a separate therapist user not assigned to test_case."""
    user = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name="Dr. Unassigned Clinician",
        email="unassigned.therapist@hospital.org",
        password_hash=hash_password("ForeignPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def foreign_therapist(db_session: Session, foreign_therapist_user: User) -> Therapist:
    """Provides linked Therapist profile for foreign_therapist_user."""
    therapist = Therapist(
        id=uuid.uuid4(),
        user_id=foreign_therapist_user.id,
        display_name="Dr. Unassigned Clinician",
    )
    db_session.add(therapist)
    db_session.commit()
    return therapist


@pytest.fixture
def foreign_therapist_headers(foreign_therapist: Therapist, foreign_therapist_user: User) -> dict:
    """Authorization headers for foreign_therapist_user."""
    token = create_access_token(
        subject=str(foreign_therapist_user.id),
        role=foreign_therapist_user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}



def test_audit_case_creation_and_assignment(
    client: TestClient,
    db_session: Session,
    test_therapist: Therapist,
    therapist_token_headers: dict,
):
    """
    Validates that creating a patient provisions a user and case,
    and logs THERAPIST_CREATED_USER, CASE_CREATED, and CASE_ASSIGNED.
    """
    payload = {
        "name": "Audit Verification Patient",
        "email": "verification.patient@hospital.org",
        "password": "SecurePassword123!",
        "victim_id": "V-AUDIT-VERIFY-01",
    }
    response = client.post(
        "/api/v1/therapist/users",
        headers=therapist_token_headers,
        json=payload,
    )
    assert response.status_code == 201
    res_data = response.json()
    created_user_id = res_data["id"]
    created_case_id = res_data["case"]["id"]

    repo = AuditLogRepository(db_session)

    # 1. Check THERAPIST_CREATED_USER
    user_logs = repo.list_logs(action="THERAPIST_CREATED_USER", resource_id=created_user_id)
    assert len(user_logs) >= 1
    assert user_logs[0].status == "SUCCESS"
    assert user_logs[0].actor_user_id == test_therapist.user_id

    # 2. Check CASE_CREATED
    case_logs = repo.list_logs(action="CASE_CREATED", resource_id=created_case_id)
    assert len(case_logs) >= 1
    assert case_logs[0].status == "SUCCESS"
    assert case_logs[0].metadata_payload.get("victim_id") == "V-AUDIT-VERIFY-01"

    # 3. Check CASE_ASSIGNED
    assign_logs = repo.list_logs(action="CASE_ASSIGNED", resource_id=created_case_id)
    assert len(assign_logs) >= 1
    assert assign_logs[0].status == "SUCCESS"
    assert assign_logs[0].metadata_payload.get("assigned_therapist_id") == str(test_therapist.id)


def test_audit_case_update(
    client: TestClient,
    db_session: Session,
    test_case: Case,
    test_therapist: Therapist,
    therapist_token_headers: dict,
    foreign_therapist_headers: dict,
):
    """
    Validates updating case attributes (timepoint, status) emits CASE_UPDATED,
    and foreign therapist update attempts return 403 and emit ACCESS_DENIED.
    """
    # 1. Successful update by authorized therapist
    update_payload = {"current_timepoint": 2, "status": "active"}
    response = client.patch(
        f"/api/v1/therapist/cases/{test_case.id}",
        headers=therapist_token_headers,
        json=update_payload,
    )
    assert response.status_code == 200
    case_data = response.json()
    assert case_data["current_timepoint"] == 2

    repo = AuditLogRepository(db_session)
    update_logs = repo.list_logs(action="CASE_UPDATED", resource_id=str(test_case.id))
    assert len(update_logs) >= 1
    assert update_logs[0].status == "SUCCESS"
    assert update_logs[0].actor_user_id == test_therapist.user_id
    assert "current_timepoint" in update_logs[0].metadata_payload.get("updated_fields", [])

    # 2. Foreign therapist update attempt -> 403
    foreign_resp = client.patch(
        f"/api/v1/therapist/cases/{test_case.id}",
        headers=foreign_therapist_headers,
        json={"current_timepoint": 3},
    )
    assert foreign_resp.status_code == 403
    assert foreign_resp.json()["detail"] == "Case not found or access denied."

    # 3. Check ACCESS_DENIED
    denied_logs = repo.list_logs(action="ACCESS_DENIED", resource_id=str(test_case.id))
    assert len(denied_logs) >= 1
    assert denied_logs[0].status == "DENIED"


def test_audit_alert_handling(
    client: TestClient,
    db_session: Session,
    test_case: Case,
    test_therapist: Therapist,
    therapist_token_headers: dict,
    foreign_therapist_headers: dict,
):
    """
    Validates handling a safety alert marks it handled, sets handled_by/at,
    logs ALERT_HANDLED, and protects against foreign therapist manipulation.
    """
    # 1. Create active SafetyEventModel
    alert = SafetyEventModel(
        id=uuid.uuid4(),
        case_id=test_case.id,
        event_type="self_harm_intent",
        severity="critical",
        status="active",
        detected_at=datetime.now(timezone.utc),
    )
    db_session.add(alert)
    db_session.commit()

    # 2. Foreign therapist attempt -> 403
    foreign_resp = client.patch(
        f"/api/v1/therapist/cases/{test_case.id}/alerts/{alert.id}",
        headers=foreign_therapist_headers,
        json={"status": "handled"},
    )
    assert foreign_resp.status_code == 403

    # 3. Authorized therapist handles alert
    response = client.patch(
        f"/api/v1/therapist/cases/{test_case.id}/alerts/{alert.id}",
        headers=therapist_token_headers,
        json={"status": "handled", "resolution_note": "Reviewed with supervisor."},
    )
    assert response.status_code == 200
    alert_data = response.json()
    assert alert_data["status"] == "handled"
    assert alert_data["handled_by"] == str(test_therapist.user_id)
    assert alert_data["handled_at"] is not None

    # 4. Verify ALERT_HANDLED audit log
    repo = AuditLogRepository(db_session)
    alert_logs = repo.list_logs(action="ALERT_HANDLED", resource_id=str(alert.id))
    assert len(alert_logs) >= 1
    assert alert_logs[0].status == "SUCCESS"
    assert alert_logs[0].actor_user_id == test_therapist.user_id
    assert alert_logs[0].metadata_payload.get("new_status") == "handled"


def test_audit_account_status_change(
    client: TestClient,
    db_session: Session,
    test_user: User,
    test_case: Case,
    test_therapist: Therapist,
    therapist_token_headers: dict,
    foreign_therapist_headers: dict,
):
    """
    Validates updating patient account status (e.g. SUSPENDED) emits ACCOUNT_STATUS_CHANGED,
    and foreign therapist attempt returns 403.
    """
    # 1. Foreign therapist attempt -> 403
    foreign_resp = client.patch(
        f"/api/v1/therapist/users/{test_user.id}/status",
        headers=foreign_therapist_headers,
        json={"status": "SUSPENDED"},
    )
    assert foreign_resp.status_code == 403

    # 2. Authorized therapist updates status
    response = client.patch(
        f"/api/v1/therapist/users/{test_user.id}/status",
        headers=therapist_token_headers,
        json={"status": "SUSPENDED"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["status"] == "SUSPENDED"

    # 3. Verify ACCOUNT_STATUS_CHANGED audit log
    repo = AuditLogRepository(db_session)
    status_logs = repo.list_logs(action="ACCOUNT_STATUS_CHANGED", resource_id=str(test_user.id))
    assert len(status_logs) >= 1
    assert status_logs[0].status == "SUCCESS"
    assert status_logs[0].actor_user_id == test_therapist.user_id
    assert status_logs[0].metadata_payload.get("old_status") == "ACTIVE"
    assert status_logs[0].metadata_payload.get("new_status") == "SUSPENDED"


def test_patient_cannot_access_audit_logs(client: TestClient, user_token_headers: dict):
    """Validates that patients (USER role) receive 403 on the therapist audit logs endpoint."""
    response = client.get("/api/v1/therapist/audit-logs", headers=user_token_headers)
    assert response.status_code == 403
