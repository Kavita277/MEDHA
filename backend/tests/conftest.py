"""
Global Test Fixtures for MEDHA Backend
======================================

Provides shared fixtures across all backend unit and integration tests:
- db_session: in-memory SQLite database session with FastAPI dependency overrides
- client: FastAPI TestClient
- test_user: Patient User fixture
- test_therapist_user: Therapist User fixture
- test_therapist: Therapist entity fixture
- test_case: Case entity fixture
- user_token_headers: Authorization header for test_user
- therapist_token_headers: Authorization header for test_therapist_user
"""

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import get_db, build_engine
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a fresh in-memory SQLite database session and overrides app get_db."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)

    def _get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    with Session(engine) as session:
        yield session

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provides a FastAPI TestClient with the test database configured."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Provides a standard test patient User entity."""
    user = User(
        id=uuid.uuid4(),
        role=UserRole.USER,
        name="Test Patient",
        email="test.patient@example.com",
        password_hash=hash_password("PatientPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_therapist_user(db_session: Session) -> User:
    """Provides a therapist User entity."""
    user = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name="Dr. Test Therapist",
        email="test.therapist@example.com",
        password_hash=hash_password("TherapistPass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_therapist(db_session: Session, test_therapist_user: User) -> Therapist:
    """Provides a Therapist entity linked to test_therapist_user."""
    therapist = Therapist(
        id=uuid.uuid4(),
        user_id=test_therapist_user.id,
        display_name="Dr. Test Therapist, Ph.D.",
    )
    db_session.add(therapist)
    db_session.commit()
    db_session.refresh(therapist)
    return therapist


@pytest.fixture
def test_case(db_session: Session, test_user: User, test_therapist: Therapist) -> Case:
    """Provides a Case entity linked to test_user and test_therapist."""
    case = Case(
        id=uuid.uuid4(),
        victim_id="V-TEST-001",
        user_id=test_user.id,
        therapist_id=test_therapist.id,
        current_timepoint=1,
        status="active",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


@pytest.fixture
def user_token_headers(test_user: User) -> dict:
    """Provides authorization headers for test_user."""
    token = create_access_token(
        subject=str(test_user.id),
        role=test_user.role.value if hasattr(test_user.role, "value") else str(test_user.role),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def therapist_token_headers(test_therapist_user: User) -> dict:
    """Provides authorization headers for test_therapist_user."""
    token = create_access_token(
        subject=str(test_therapist_user.id),
        role=test_therapist_user.role.value if hasattr(test_therapist_user.role, "value") else str(test_therapist_user.role),
    )
    return {"Authorization": f"Bearer {token}"}
