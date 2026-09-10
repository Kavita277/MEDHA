"""
Case Service Tests
==================

Unit tests for CaseService queries and role-based access verification.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.persistence.repositories.user import UserRepository
from backend.services.case_service import CaseService


@pytest.fixture
def db_session():
    """Provides an isolated transactional SQLite session."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_case_service_queries_and_access_verification(db_session: Session):
    """Verifies CaseService retrieval methods and access rule checks."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)
    case_service = CaseService(db_session)

    # 1. Setup Patient A, Patient B, Therapist A, Therapist B
    p_a = user_repo.add(User(name="PA", email="pa@example.com", role=UserRole.USER, password_hash="h"))
    p_b = user_repo.add(User(name="PB", email="pb@example.com", role=UserRole.USER, password_hash="h"))
    
    t_user_a = user_repo.add(User(name="TA", email="ta@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist_a = therapist_repo.add(Therapist(user_id=t_user_a.id, display_name="Dr. TA"))

    t_user_b = user_repo.add(User(name="TB", email="tb@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist_b = therapist_repo.add(Therapist(user_id=t_user_b.id, display_name="Dr. TB"))

    # Case A: p_a assigned to therapist_a
    case_a = case_repo.add(Case(victim_id="V-SRV-A", user_id=p_a.id, therapist_id=therapist_a.id, current_timepoint=1))

    # 2. Test lookups
    by_id = case_service.get_case(case_a.id)
    assert by_id is not None
    assert by_id.victim_id == "V-SRV-A"

    by_victim = case_service.get_case_by_victim_id("V-SRV-A")
    assert by_victim is not None
    assert by_victim.id == case_a.id

    active_p_a = case_service.get_active_case_for_user(p_a.id)
    assert active_p_a is not None
    assert active_p_a.id == case_a.id

    assert case_service.get_active_case_for_user(p_b.id) is None

    t_cases = case_service.list_cases_for_therapist(therapist_a.id)
    assert len(t_cases) == 1
    assert t_cases[0].id == case_a.id

    # 3. Test verify_case_access
    # Patient A owns Case A -> True
    assert case_service.verify_case_access(p_a, case_a) is True
    # Patient B does not own Case A -> False
    assert case_service.verify_case_access(p_b, case_a) is False

    # Therapist A is assigned to Case A -> True
    assert case_service.verify_case_access(t_user_a, case_a) is True
    # Therapist B is not assigned to Case A -> False
    assert case_service.verify_case_access(t_user_b, case_a) is False
