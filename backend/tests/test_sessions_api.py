"""
Sessions API Tests
==================

Functional API tests verifying:
- POST /api/v1/sessions: Patient and Therapist session creation
- Strict Case Ownership & RBAC:
  - User isolation: Patient A cannot access Patient B's session (403 Forbidden)
  - Therapist isolation: Therapist B cannot access Therapist A's patient session (403 Forbidden)
  - Unauthenticated access rejected (401 Unauthorized)
- UUID and session_identifier lookup compatibility
- POST /api/v1/sessions/{session_id}/end: Session conclusion lifecycle
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.dependencies import get_db
from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.security.passwords import hash_password


@pytest.fixture
def session_api_db():
    """Sets up an in-memory SQLite database populated with two distinct therapist-case-patient silos."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    # Seed two clinical silos:
    # Silo A: Therapist A, Patient A, Case A
    # Silo B: Therapist B, Patient B, Case B
    with Session(engine) as session:
        # Silo A
        patient_a = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Alpha",
            email="patient.alpha@medha.org",
            password_hash=hash_password("PassAlpha123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_user_a = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Alpha",
            email="dr.alpha@medha.org",
            password_hash=hash_password("DocAlpha123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_a = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_a.id,
            display_name="Dr. Alpha, M.D.",
        )
        case_a = Case(
            id=uuid.uuid4(),
            victim_id="V-ALPHA-001",
            user_id=patient_a.id,
            therapist_id=therapist_a.id,
            current_timepoint=1,
            status="active",
        )

        # Silo B
        patient_b = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Patient Beta",
            email="patient.beta@medha.org",
            password_hash=hash_password("PassBeta123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_user_b = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Beta",
            email="dr.beta@medha.org",
            password_hash=hash_password("DocBeta123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_b = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_b.id,
            display_name="Dr. Beta, Ph.D.",
        )
        case_b = Case(
            id=uuid.uuid4(),
            victim_id="V-BETA-001",
            user_id=patient_b.id,
            therapist_id=therapist_b.id,
            current_timepoint=2,
            status="active",
        )

        session.add_all([
            patient_a, therapist_user_a, therapist_a, case_a,
            patient_b, therapist_user_b, therapist_b, case_b,
        ])
        session.commit()
        case_a_id = str(case_a.id)
        case_b_id = str(case_b.id)

    yield {
        "engine": engine,
        "case_a_id": case_a_id,
        "case_b_id": case_b_id,
    }

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(session_api_db):
    """Provides a TestClient wired to the test DB."""
    with TestClient(app) as test_client:
        yield test_client


def get_token(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and return a JWT access token."""
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


def test_patient_create_session_success(client, session_api_db):
    """Verifies that an authenticated patient can create a session for their active case."""
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")

    response = client.post(
        "/api/v1/sessions",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()

    assert data["case_id"] == session_api_db["case_a_id"]
    assert data["victim_id"] == "V-ALPHA-001"
    assert data["timepoint"] == 1
    assert data["status"] == "ACTIVE"
    assert data["session_identifier"].startswith("sess_")
    assert "state_summary" in data


def test_patient_create_session_custom_identifier(client, session_api_db):
    """Verifies that a custom session identifier is honored."""
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")

    response = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "custom_patient_session_99"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["session_identifier"] == "custom_patient_session_99"


def test_therapist_create_session_success(client, session_api_db):
    """Verifies that an authenticated therapist can create a session for an assigned case."""
    token = get_token(client, "dr.alpha@medha.org", "DocAlpha123!")

    response = client.post(
        "/api/v1/sessions",
        json={"case_id": session_api_db["case_a_id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == session_api_db["case_a_id"]
    assert data["victim_id"] == "V-ALPHA-001"


def test_therapist_create_session_unassigned_case_forbidden(client, session_api_db):
    """Verifies that Therapist A cannot create a session for Therapist B's case."""
    token_a = get_token(client, "dr.alpha@medha.org", "DocAlpha123!")

    response = client.post(
        "/api/v1/sessions",
        json={"case_id": session_api_db["case_b_id"]},  # Case B belongs to Therapist B
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


def test_patient_session_access_and_isolation(client):
    """
    Verifies that:
    1. Patient A can read Patient A's session.
    2. Patient B attempting to access Patient A's session receives 403 Forbidden.
    """
    token_a = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    token_b = get_token(client, "patient.beta@medha.org", "PassBeta123!")

    # Patient A creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_isolation_a"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # 1. Patient A accesses by UUID
    res_a_uuid = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_uuid.status_code == 200
    assert res_a_uuid.json()["session_identifier"] == "sess_isolation_a"

    # 2. Patient A accesses by string identifier
    res_a_ident = client.get("/api/v1/sessions/sess_isolation_a", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_ident.status_code == 200

    # 3. Patient B attempts to access Patient A's session -> 403 Forbidden
    res_b = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 403
    assert "access denied" in res_b.json()["detail"].lower()


def test_therapist_session_access_and_isolation(client):
    """
    Verifies that:
    1. Assigned Therapist A can access Patient A's session.
    2. Unassigned Therapist B attempting to access Patient A's session receives 403 Forbidden.
    """
    token_patient_a = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    token_therapist_a = get_token(client, "dr.alpha@medha.org", "DocAlpha123!")
    token_therapist_b = get_token(client, "dr.beta@medha.org", "DocBeta123!")

    # Patient A creates session
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_therapist_test"},
        headers={"Authorization": f"Bearer {token_patient_a}"},
    )
    session_id = create_resp.json()["id"]

    # 1. Assigned Therapist A accesses Patient A's session -> 200 OK
    res_t_a = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {token_therapist_a}"})
    assert res_t_a.status_code == 200
    assert res_t_a.json()["session_identifier"] == "sess_therapist_test"

    # 2. Unassigned Therapist B accesses Patient A's session -> 403 Forbidden
    res_t_b = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {token_therapist_b}"})
    assert res_t_b.status_code == 403
    assert "access denied" in res_t_b.json()["detail"].lower()


def test_unauthenticated_session_access(client):
    """Verifies that unauthenticated requests receive 401 Unauthorized."""
    response = client.get("/api/v1/sessions/any_session_id")
    assert response.status_code == 401


def test_nonexistent_session_access(client):
    """Verifies that accessing a nonexistent session returns 404 Not Found."""
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")
    response = client.get(
        "/api/v1/sessions/sess_does_not_exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_end_session_endpoint(client):
    """Verifies that ending a session marks it ENDED and sets closed_at."""
    token = get_token(client, "patient.alpha@medha.org", "PassAlpha123!")

    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_identifier": "sess_to_end"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = create_resp.json()["id"]

    end_resp = client.post(
        f"/api/v1/sessions/{session_id}/end",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert end_resp.status_code == 200
    data = end_resp.json()
    assert data["status"] == "ENDED"
    assert data["closed_at"] is not None
