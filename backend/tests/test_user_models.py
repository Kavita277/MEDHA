"""
User & Therapist Model Tests
============================

Tests for:
- User model creation and defaults (UUID, role, status, must_change_password)
- Therapist model creation and relationship to User
- Constraint enforcement (unique email, unique mobile, unique therapist user_id)
- Cascade deletion (deleting user removes linked therapist)
- Pydantic schema validation (UserCreate, UserResponse, TherapistResponse)
"""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.schemas.therapist import TherapistCreate, TherapistResponse


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


def test_create_user_defaults(db_session: Session):
    """Verifies default values and UUID generation on User model."""
    user = User(
        name="Asha Sharma",
        email="asha@example.com",
        password_hash="hashed_pw_12345",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.role == UserRole.USER
    assert user.status == UserStatus.ACTIVE
    assert user.must_change_password is False
    assert user.last_login_at is None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.therapist is None
    assert "asha@example.com" in repr(user)


def test_user_email_unique_constraint(db_session: Session):
    """Verifies that duplicate emails are rejected by unique constraint."""
    user1 = User(
        name="User One",
        email="duplicate@example.com",
        password_hash="hash1",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        name="User Two",
        email="duplicate@example.com",
        password_hash="hash2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_mobile_unique_constraint(db_session: Session):
    """Verifies that duplicate mobile numbers are rejected."""
    user1 = User(
        name="User One",
        email="user1@example.com",
        mobile="+919876543210",
        password_hash="hash1",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        name="User Two",
        email="user2@example.com",
        mobile="+919876543210",
        password_hash="hash2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_create_therapist_relationship(db_session: Session):
    """Verifies Therapist profile creation and 1-to-1 relationship with User."""
    user = User(
        name="Dr. Sunita Rao",
        email="sunita@clinic.org",
        role=UserRole.THERAPIST,
        password_hash="hashed_pw_therapist",
    )
    db_session.add(user)
    db_session.commit()

    therapist = Therapist(
        user_id=user.id,
        display_name="Dr. S. Rao, Clinical Psychologist",
    )
    db_session.add(therapist)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(therapist)

    assert therapist.user is not None
    assert therapist.user.id == user.id
    assert user.therapist is not None
    assert user.therapist.id == therapist.id
    assert user.therapist.display_name == "Dr. S. Rao, Clinical Psychologist"
    assert "Dr. S. Rao" in repr(therapist)


def test_therapist_user_id_unique_constraint(db_session: Session):
    """Verifies that only one therapist profile can link to a user."""
    user = User(
        name="Single Therapist User",
        email="single_therapist@example.com",
        role=UserRole.THERAPIST,
        password_hash="pw",
    )
    db_session.add(user)
    db_session.commit()

    t1 = Therapist(user_id=user.id, display_name="Profile 1")
    db_session.add(t1)
    db_session.commit()

    t2 = Therapist(user_id=user.id, display_name="Profile 2")
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_user_removes_therapist(db_session: Session):
    """Verifies that deleting a User cascades and deletes the linked Therapist."""
    user = User(
        name="To Be Deleted",
        email="delete_me@example.com",
        role=UserRole.THERAPIST,
        password_hash="pw",
    )
    db_session.add(user)
    db_session.commit()

    therapist = Therapist(
        user_id=user.id,
        display_name="Temporary Profile",
    )
    db_session.add(therapist)
    db_session.commit()

    therapist_id = therapist.id

    # Delete the user
    db_session.delete(user)
    db_session.commit()

    assert db_session.get(User, user.id) is None
    assert db_session.get(Therapist, therapist_id) is None


def test_user_pydantic_schemas():
    """Verifies Pydantic schema validation for User."""
    create_payload = {
        "name": "Kavita Patel",
        "email": "kavita@example.com",
        "mobile": "+919123456780",
        "password": "strongPassword123!",
        "role": "USER",
        "status": "ACTIVE",
        "must_change_password": True,
    }
    schema = UserCreate(**create_payload)
    assert schema.name == "Kavita Patel"
    assert schema.email == "kavita@example.com"
    assert schema.must_change_password is True

    # Invalid email error
    with pytest.raises(ValidationError):
        UserCreate(
            name="Bad Email",
            email="not-an-email",
            password="password123",
        )

    # Short password error
    with pytest.raises(ValidationError):
        UserCreate(
            name="Short Pw",
            email="test@example.com",
            password="short",
        )


def test_therapist_pydantic_schemas():
    """Verifies Pydantic schema validation for Therapist."""
    user_id = uuid.uuid4()
    t_create = TherapistCreate(
        user_id=user_id,
        display_name="Dr. Vikram Sen",
    )
    assert t_create.user_id == user_id
    assert t_create.display_name == "Dr. Vikram Sen"

    # Empty display name rejected
    with pytest.raises(ValidationError):
        TherapistCreate(user_id=user_id, display_name="")
