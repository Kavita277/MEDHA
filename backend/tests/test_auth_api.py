"""
Authentication API Tests
========================

Functional API tests verifying:
- POST /api/v1/auth/login with valid/invalid credentials, active/suspended/deactivated accounts
- GET /api/v1/auth/me token authorization and user profile retrieval
- Password hash confidentiality (never returned in responses)
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
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.security.passwords import hash_password


@pytest.fixture
def auth_db():
    """Sets up an in-memory SQLite database for API testing."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    # Seed test users
    with Session(engine) as session:
        # Active User
        user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="John Patient",
            email="patient@medha.org",
            mobile="+919876543201",
            password_hash=hash_password("PatientPass123!"),
            status=UserStatus.ACTIVE,
        )
        # Active Therapist
        therapist_user = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Jane Clinician",
            email="therapist@medha.org",
            mobile="+919876543202",
            password_hash=hash_password("TherapistPass123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_profile = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user.id,
            display_name="Dr. Jane Clinician, Psy.D.",
        )
        # Suspended User
        suspended_user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Suspended Patient",
            email="suspended@medha.org",
            password_hash=hash_password("SuspendedPass123!"),
            status=UserStatus.SUSPENDED,
        )
        # Deactivated User
        deactivated_user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Deactivated Patient",
            email="deactivated@medha.org",
            password_hash=hash_password("DeactivatedPass123!"),
            status=UserStatus.DEACTIVATED,
        )

        session.add_all([user, therapist_user, therapist_profile, suspended_user, deactivated_user])
        session.commit()

    yield engine

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(auth_db):
    """Provides a test client configured with the test database."""
    with TestClient(app) as test_client:
        yield test_client


def test_login_success_active_user(client):
    """Verifies successful login for active user returning JWT token and profile without password hash."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@medha.org", "password": "PatientPass123!"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert "user" in data

    user_info = data["user"]
    assert user_info["email"] == "patient@medha.org"
    assert user_info["role"] == "USER"
    assert user_info["status"] == "ACTIVE"
    assert "password_hash" not in user_info
    assert "password" not in user_info
    assert user_info["last_login_at"] is not None


def test_login_success_therapist(client):
    """Verifies successful login for clinician with THERAPIST role."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "therapist@medha.org", "password": "TherapistPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "THERAPIST"


def test_login_invalid_password(client):
    """Verifies rejection of invalid password with 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@medha.org", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Verifies rejection of unknown user with 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@medha.org", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_suspended_account(client):
    """Verifies rejection of suspended account with 403 Forbidden."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "suspended@medha.org", "password": "SuspendedPass123!"},
    )
    assert response.status_code == 403
    assert "suspended" in response.json()["detail"].lower()


def test_login_deactivated_account(client):
    """Verifies rejection of deactivated account with 403 Forbidden."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "deactivated@medha.org", "password": "DeactivatedPass123!"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


def test_get_me_authorized(client):
    """Verifies GET /api/v1/auth/me returns current user profile when authenticated."""
    # 1. Login to obtain token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@medha.org", "password": "PatientPass123!"},
    )
    token = login_resp.json()["access_token"]

    # 2. Call /me with Bearer token
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "patient@medha.org"
    assert user_data["role"] == "USER"
    assert "password_hash" not in user_data


def test_get_me_unauthorized_missing_token(client):
    """Verifies GET /api/v1/auth/me returns 401 when Authorization header is missing."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """Verifies GET /api/v1/auth/me returns 401 when token is invalid or malformed."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401
