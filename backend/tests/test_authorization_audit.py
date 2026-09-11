"""
Step 27 3-Layer RBAC and Anti-Enumeration Authorization Security Tests
======================================================================

Validates the full authorization matrix across MEDHA therapist decision support
and clinical results endpoints:
  - Layer 1: JWT Authentication (401 if missing/invalid/expired)
  - Layer 2: Role-Based Access Control (403 if USER / patient attempts therapist API)
  - Layer 3: Clinical Case Ownership & Anti-Enumeration (403 if foreign case / non-existent case)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


@pytest.fixture
def test_session(db_session: Session, test_case: Case) -> SessionModel:
    """Provides a SessionModel linked to test_case."""
    sess = SessionModel(
        id=uuid.uuid4(),
        session_identifier=f"SESS-{uuid.uuid4().hex[:8].upper()}",
        case_id=test_case.id,
        timepoint=1,
        status=SessionStatus.ACTIVE,
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


@pytest.fixture
def foreign_therapist_headers(db_session: Session) -> dict:
    """Provides authorization headers for a distinct, unassociated therapist."""
    user = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name="Dr. Foreign Clinician",
        email="foreign.therapist@hospital.org",
        password_hash=hash_password("ForeignPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()

    therapist = Therapist(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name="Dr. Foreign Clinician",
    )
    db_session.add(therapist)
    db_session.commit()

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "path_template",
    [
        "/api/v1/therapist/cases/{case_id}/results",
        "/api/v1/therapist/cases/{case_id}/sessions",
        "/api/v1/therapist/cases/{case_id}/checkins",
        "/api/v1/therapist/cases/{case_id}/behaviour",
        "/api/v1/therapist/cases/{case_id}/alerts",
        "/api/v1/therapist/cases/{case_id}/insights",
        "/api/v1/therapist/cases/{case_id}/recommendations",
        "/api/v1/therapist/cases/{case_id}/safety-protocol",
    ],
)
def test_rbac_case_endpoints_full_matrix(
    client: TestClient,
    db_session: Session,
    test_case: Case,
    user_token_headers: dict,
    therapist_token_headers: dict,
    foreign_therapist_headers: dict,
    path_template: str,
):
    """
    Tests Layer 1, 2, and 3 access controls for each case-level therapist endpoint.
    """
    url = path_template.format(case_id=test_case.id)

    # 1. Unauthenticated -> 401
    resp_unauth = client.get(url)
    assert resp_unauth.status_code == 401

    # 2. Patient role (USER) -> 403 (Layer 2)
    resp_patient = client.get(url, headers=user_token_headers)
    assert resp_patient.status_code == 403

    # 3. Foreign Therapist -> 403 (Layer 3 & Anti-enumeration)
    resp_foreign = client.get(url, headers=foreign_therapist_headers)
    assert resp_foreign.status_code == 403
    assert resp_foreign.json()["detail"] == "Case not found or access denied."

    # 4. Non-existent Case ID by authorized therapist -> 403 (anti-enumeration)
    non_existent_url = path_template.format(case_id=uuid.uuid4())
    resp_nonexistent = client.get(non_existent_url, headers=therapist_token_headers)
    assert resp_nonexistent.status_code == 403
    assert resp_nonexistent.json()["detail"] == "Case not found or access denied."

    # 5. Authorized Therapist -> 200 (Success)
    resp_auth = client.get(url, headers=therapist_token_headers)
    assert resp_auth.status_code == 200


@pytest.mark.parametrize(
    "path_template",
    [
        "/api/v1/therapist/sessions/{session_id}/results",
        "/api/v1/therapist/sessions/{session_id}/insights",
        "/api/v1/therapist/sessions/{session_id}/recommendations",
        "/api/v1/therapist/sessions/{session_id}/safety-protocol",
    ],
)
def test_rbac_session_endpoints_full_matrix(
    client: TestClient,
    db_session: Session,
    test_session: SessionModel,
    user_token_headers: dict,
    therapist_token_headers: dict,
    foreign_therapist_headers: dict,
    path_template: str,
):
    """
    Tests Layer 1, 2, and 3 access controls for each session-level therapist endpoint.
    """
    url = path_template.format(session_id=test_session.id)

    # 1. Unauthenticated -> 401
    resp_unauth = client.get(url)
    assert resp_unauth.status_code == 401

    # 2. Patient role (USER) -> 403
    resp_patient = client.get(url, headers=user_token_headers)
    assert resp_patient.status_code == 403

    # 3. Foreign Therapist -> 403
    resp_foreign = client.get(url, headers=foreign_therapist_headers)
    assert resp_foreign.status_code == 403

    # 4. Non-existent Session ID -> 403 (anti-enumeration)
    non_existent_url = path_template.format(session_id=uuid.uuid4())
    resp_nonexistent = client.get(non_existent_url, headers=therapist_token_headers)
    assert resp_nonexistent.status_code == 403

    # 5. Authorized Therapist -> 200
    resp_auth = client.get(url, headers=therapist_token_headers)
    assert resp_auth.status_code == 200
