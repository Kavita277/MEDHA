"""
Account Repository Tests
========================

Tests for UserRepository and TherapistRepository CRUD and specialized queries.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.repositories.user import UserRepository
from backend.persistence.repositories.therapist import TherapistRepository


@pytest.fixture
def sqlite_engine():
    """Provides an SQLite in-memory engine with all tables created."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(sqlite_engine):
    """Provides a fresh transactional session for each test."""
    with Session(sqlite_engine) as session:
        yield session


def test_user_repository_crud_and_lookups(db_session: Session):
    """Verifies UserRepository CRUD and specialized lookup methods."""
    user_repo = UserRepository(db_session)

    user1 = User(
        name="Patient One",
        email="patient1@medha.org",
        mobile="+919876543201",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        password_hash="hashed_pw_1",
    )
    user2 = User(
        name="Therapist One",
        email="therapist1@medha.org",
        mobile="+919876543202",
        role=UserRole.THERAPIST,
        status=UserStatus.SUSPENDED,
        password_hash="hashed_pw_2",
    )

    # 1. Add
    user_repo.add(user1)
    user_repo.add(user2)

    # 2. Get by ID
    fetched = user_repo.get(user1.id)
    assert fetched is not None
    assert fetched.name == "Patient One"

    # 3. Get by Email
    by_email = user_repo.get_by_email("patient1@medha.org")
    assert by_email is not None
    assert by_email.id == user1.id

    by_missing_email = user_repo.get_by_email("missing@medha.org")
    assert by_missing_email is None

    # 4. Get by Mobile
    by_mobile = user_repo.get_by_mobile("+919876543202")
    assert by_mobile is not None
    assert by_mobile.id == user2.id

    # 5. List by Role
    users_only = user_repo.list_by_role(UserRole.USER)
    assert len(users_only) == 1
    assert users_only[0].email == "patient1@medha.org"

    therapists_only = user_repo.list_by_role(UserRole.THERAPIST)
    assert len(therapists_only) == 1
    assert therapists_only[0].email == "therapist1@medha.org"

    # 6. List by Status
    active_users = user_repo.list_by_status(UserStatus.ACTIVE)
    assert len(active_users) == 1

    suspended_users = user_repo.list_by_status(UserStatus.SUSPENDED)
    assert len(suspended_users) == 1

    # 7. Delete
    user_repo.delete(user1)
    assert user_repo.get(user1.id) is None
    assert user_repo.get_by_email("patient1@medha.org") is None


def test_therapist_repository_crud_and_lookups(db_session: Session):
    """Verifies TherapistRepository CRUD and relationship eager loading."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)

    user = User(
        name="Dr. Clinical Lead",
        email="lead@medha.org",
        role=UserRole.THERAPIST,
        password_hash="secure_hash",
    )
    user_repo.add(user)

    therapist = Therapist(
        user_id=user.id,
        display_name="Dr. Clinical Lead, Ph.D.",
    )
    therapist_repo.add(therapist)

    # 1. Get by ID
    fetched_t = therapist_repo.get(therapist.id)
    assert fetched_t is not None
    assert fetched_t.display_name == "Dr. Clinical Lead, Ph.D."

    # 2. Get by user_id
    by_uid = therapist_repo.get_by_user_id(user.id)
    assert by_uid is not None
    assert by_uid.id == therapist.id

    # 3. Get with user eagerly loaded
    with_user = therapist_repo.get_with_user(therapist.id)
    assert with_user is not None
    assert with_user.user is not None
    assert with_user.user.email == "lead@medha.org"

    # 4. Delete therapist
    therapist_repo.delete(therapist)
    assert therapist_repo.get(therapist.id) is None
    # User still exists
    assert user_repo.get(user.id) is not None
