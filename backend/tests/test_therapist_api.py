"""
Therapist API Tests
===================

Functional tests verifying:
- POST /api/v1/therapist/users: Patient user account and case creation by authenticated therapist
- Password confidentiality: plain passwords hashed, hashes never returned
- Role boundaries: regular USER receives 403 Forbidden
- Unauthenticated requests receive 401 Unauthorized
- Strict data isolation: Therapist A cannot see Therapist B's patients in GET /api/v1/therapist/users
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
from backend.persistence.models.case import Case
from backend.security.passwords import hash_password, verify_password


@pytest.fixture
def therapist_test_db():
    """Sets up an in-memory database with two distinct therapists and one regular user."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    # Seed users
    with Session(engine) as session:
        # Regular Patient User
        regular_user = User(
            id=uuid.uuid4(),
            role=UserRole.USER,
            name="Regular Patient",
            email="patient@medha.org",
            password_hash=hash_password("PatientPass123!"),
            status=UserStatus.ACTIVE,
        )

        # Therapist A
        therapist_user_a = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Therapist Alpha",
            email="alpha@medha.org",
            password_hash=hash_password("TherapistPassA123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_profile_a = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_a.id,
            display_name="Dr. Therapist Alpha, MD",
        )

        # Therapist B
        therapist_user_b = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name="Dr. Therapist Beta",
            email="beta@medha.org",
            password_hash=hash_password("TherapistPassB123!"),
            status=UserStatus.ACTIVE,
        )
        therapist_profile_b = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user_b.id,
            display_name="Dr. Therapist Beta, PhD",
        )

        session.add_all([
            regular_user,
            therapist_user_a, therapist_profile_a,
            therapist_user_b, therapist_profile_b,
        ])
        session.commit()

    yield engine

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(therapist_test_db):
    """Provides a test client configured with test database."""
    with TestClient(app) as test_client:
        yield test_client


def get_token(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and return a bearer access token."""
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


def test_therapist_create_patient_success(client, therapist_test_db):
    """Verifies that an authenticated therapist can create a patient account and linked case."""
    token_a = get_token(client, "alpha@medha.org", "TherapistPassA123!")

    payload = {
        "name": "Jane Patient",
        "email": "jane.patient@example.com",
        "password": "SecurePassword987!",
        "mobile": "+919811122233",
        "victim_id": "V-JANE-01",
    }

    response = client.post(
        "/api/v1/therapist/users",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201
    data = response.json()

    # 1. Check user attributes
    assert data["name"] == "Jane Patient"
    assert data["email"] == "jane.patient@example.com"
    assert data["role"] == "USER"
    assert data["status"] == "ACTIVE"
    assert data["must_change_password"] is True
    assert "password_hash" not in data
    assert "password" not in data

    # 2. Check case attributes
    assert "case" in data
    assert data["case"]["victim_id"] == "V-JANE-01"
    assert data["case"]["current_timepoint"] == 1
    assert data["case"]["status"] == "active"

    # 3. Verify in database: password is hash, not plaintext
    with Session(therapist_test_db) as session:
        created_user = session.query(User).filter(User.email == "jane.patient@example.com").first()
        assert created_user is not None
        assert created_user.password_hash != "SecurePassword987!"
        assert verify_password("SecurePassword987!", created_user.password_hash) is True

        linked_case = session.query(Case).filter(Case.victim_id == "V-JANE-01").first()
        assert linked_case is not None
        assert linked_case.user_id == created_user.id


def test_therapist_create_patient_auto_victim_id(client):
    """Verifies that victim_id is auto-generated if not supplied."""
    token_a = get_token(client, "alpha@medha.org", "TherapistPassA123!")

    payload = {
        "name": "Auto ID Patient",
        "email": "autoid@example.com",
        "password": "SecurePassword987!",
    }

    response = client.post(
        "/api/v1/therapist/users",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["case"]["victim_id"].startswith("V-")


def test_therapist_create_patient_duplicate_email(client):
    """Verifies that creating a patient with an existing email returns 400."""
    token_a = get_token(client, "alpha@medha.org", "TherapistPassA123!")

    payload = {
        "name": "Duplicate Email Patient",
        "email": "patient@medha.org",  # already exists
        "password": "Password123!",
    }

    response = client.post(
        "/api/v1/therapist/users",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_regular_user_cannot_create_patient(client):
    """Verifies that a user with USER role cannot access therapist endpoints (403 Forbidden)."""
    user_token = get_token(client, "patient@medha.org", "PatientPass123!")

    payload = {
        "name": "Unauthorized Patient",
        "email": "unauthorized@example.com",
        "password": "Password123!",
    }

    response = client.post(
        "/api/v1/therapist/users",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert "insufficient permissions" in response.json()["detail"].lower()


def test_unauthenticated_cannot_create_patient(client):
    """Verifies unauthenticated calls return 401 Unauthorized."""
    response = client.post(
        "/api/v1/therapist/users",
        json={"name": "X", "email": "x@medha.org", "password": "Password123!"},
    )
    assert response.status_code == 401


def test_therapist_patient_listing_and_strict_isolation(client):
    """
    Verifies that Therapist A only sees patients assigned to Therapist A,
    and Therapist B only sees patients assigned to Therapist B.
    """
    token_a = get_token(client, "alpha@medha.org", "TherapistPassA123!")
    token_b = get_token(client, "beta@medha.org", "TherapistPassB123!")

    # 1. Therapist A creates Patient A1 and Patient A2
    client.post(
        "/api/v1/therapist/users",
        json={"name": "Patient Alpha One", "email": "a1@example.com", "password": "Pass123456!"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    client.post(
        "/api/v1/therapist/users",
        json={"name": "Patient Alpha Two", "email": "a2@example.com", "password": "Pass123456!"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # 2. Therapist B creates Patient B1
    client.post(
        "/api/v1/therapist/users",
        json={"name": "Patient Beta One", "email": "b1@example.com", "password": "Pass123456!"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # 3. Therapist A queries patients
    res_a = client.get("/api/v1/therapist/users", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    patients_a = res_a.json()
    emails_a = [p["email"] for p in patients_a]

    assert "a1@example.com" in emails_a
    assert "a2@example.com" in emails_a
    assert "b1@example.com" not in emails_a  # Strict isolation!
    assert len(patients_a) == 2

    # 4. Therapist B queries patients
    res_b = client.get("/api/v1/therapist/users", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    patients_b = res_b.json()
    emails_b = [p["email"] for p in patients_b]

    assert "b1@example.com" in emails_b
    assert "a1@example.com" not in emails_b  # Strict isolation!
    assert "a2@example.com" not in emails_b  # Strict isolation!
    assert len(patients_b) == 1


def test_regular_user_cannot_list_therapist_patients(client):
    """Verifies that a regular user cannot list patients (403 Forbidden)."""
    user_token = get_token(client, "patient@medha.org", "PatientPass123!")
    response = client.get("/api/v1/therapist/users", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
