"""
Case Model & Repository Tests
=============================

Unit tests verifying Case model persistence, relationship wiring, unique constraints,
and CaseRepository queries.
"""

import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.persistence.repositories.user import UserRepository


@pytest.fixture
def db_session():
    """Provides a fresh transactional session with SQLite in-memory database."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_case_creation_and_relationships(db_session: Session):
    """Verifies Case persistence and navigation to User and Therapist relationships."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)

    # 1. Create Patient User
    patient = User(
        name="Patient Case Test",
        email="patient.case@example.com",
        role=UserRole.USER,
        password_hash="hash",
    )
    user_repo.add(patient)

    # 2. Create Therapist
    therapist_user = User(
        name="Therapist Case Test",
        email="therapist.case@example.com",
        role=UserRole.THERAPIST,
        password_hash="hash",
    )
    user_repo.add(therapist_user)

    therapist = Therapist(
        user_id=therapist_user.id,
        display_name="Dr. Case Tester",
    )
    therapist_repo.add(therapist)

    # 3. Create Case
    case = Case(
        victim_id="V-TEST-001",
        user_id=patient.id,
        therapist_id=therapist.id,
        current_timepoint=1,
        status="active",
    )
    case_repo.add(case)

    # 4. Verify retrieval & relationships
    fetched_case = case_repo.get(case.id)
    assert fetched_case is not None
    assert fetched_case.victim_id == "V-TEST-001"
    assert fetched_case.user.id == patient.id
    assert fetched_case.therapist.id == therapist.id
    assert fetched_case.user.name == "Patient Case Test"
    assert fetched_case.therapist.display_name == "Dr. Case Tester"


def test_case_repository_queries(db_session: Session):
    """Verifies specialized lookup methods on CaseRepository."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)

    # Seed Patient and Therapist
    patient = user_repo.add(User(name="Patient Q", email="patient.q@example.com", role=UserRole.USER, password_hash="h"))
    therapist_user = user_repo.add(User(name="Therapist Q", email="therapist.q@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist = therapist_repo.add(Therapist(user_id=therapist_user.id, display_name="Dr. Q"))

    case = case_repo.add(Case(victim_id="V-Q-001", user_id=patient.id, therapist_id=therapist.id))

    # 1. get_by_victim_id
    by_victim = case_repo.get_by_victim_id("V-Q-001")
    assert by_victim is not None
    assert by_victim.id == case.id
    assert case_repo.get_by_victim_id("NONEXISTENT") is None

    # 2. get_active_case_for_user
    active_case = case_repo.get_active_case_for_user(patient.id)
    assert active_case is not None
    assert active_case.victim_id == "V-Q-001"

    # 3. list_cases_for_therapist
    cases = case_repo.list_cases_for_therapist(therapist.id)
    assert len(cases) == 1
    assert cases[0].id == case.id

    # 4. list_users_for_therapist
    users = case_repo.list_users_for_therapist(therapist.id)
    assert len(users) == 1
    assert users[0].id == patient.id

    # 5. get_therapist_patient
    assigned = case_repo.get_therapist_patient(therapist.id, patient.id)
    assert assigned is not None
    assert assigned.id == patient.id

    unassigned = case_repo.get_therapist_patient(uuid.uuid4(), patient.id)
    assert unassigned is None


def test_case_victim_id_unique_constraint(db_session: Session):
    """Verifies that duplicate victim_id raises IntegrityError."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)

    patient1 = user_repo.add(User(name="P1", email="p1@example.com", role=UserRole.USER, password_hash="h"))
    patient2 = user_repo.add(User(name="P2", email="p2@example.com", role=UserRole.USER, password_hash="h"))
    therapist_user = user_repo.add(User(name="T1", email="t1@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist = therapist_repo.add(Therapist(user_id=therapist_user.id, display_name="Dr. T"))

    case_repo.add(Case(victim_id="V-DUPLICATE", user_id=patient1.id, therapist_id=therapist.id))

    with pytest.raises(IntegrityError):
        case_repo.add(Case(victim_id="V-DUPLICATE", user_id=patient2.id, therapist_id=therapist.id))
