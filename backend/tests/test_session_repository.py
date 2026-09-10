"""
Session Repository Tests
========================

Unit tests for SessionRepository CRUD operations and specialized queries.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.persistence.repositories.user import UserRepository


@pytest.fixture
def db_session():
    """Provides an isolated transactional SQLite session."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_session_repository_crud_and_lookups(db_session: Session):
    """Verifies SessionRepository CRUD, lookups by identifier and UUID, and status transitions."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)
    session_repo = SessionRepository(db_session)

    # 1. Setup Patient, Therapist, and Case
    patient = user_repo.add(User(name="P", email="p@example.com", role=UserRole.USER, password_hash="h"))
    t_user = user_repo.add(User(name="T", email="t@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist = therapist_repo.add(Therapist(user_id=t_user.id, display_name="Dr. T"))
    case = case_repo.add(Case(victim_id="V-SESS-01", user_id=patient.id, therapist_id=therapist.id))

    # 2. Add Session
    session1 = SessionModel(
        id=uuid.uuid4(),
        case_id=case.id,
        session_identifier="sess_repo_test_01",
        timepoint=1,
        status=SessionStatus.ACTIVE.value,
        state_snapshot={"victim_id": "V-SESS-01", "timepoint": 1},
    )
    session_repo.add(session1)

    # 3. Get by UUID
    fetched_by_id = session_repo.get(session1.id)
    assert fetched_by_id is not None
    assert fetched_by_id.session_identifier == "sess_repo_test_01"

    # 4. Get by session_identifier
    by_identifier = session_repo.get_by_identifier("sess_repo_test_01")
    assert by_identifier is not None
    assert by_identifier.id == session1.id

    # 5. Flexible get_by_id_or_identifier
    by_uuid_flex = session_repo.get_by_id_or_identifier(session1.id)
    assert by_uuid_flex is not None
    assert by_uuid_flex.id == session1.id

    by_str_uuid_flex = session_repo.get_by_id_or_identifier(str(session1.id))
    assert by_str_uuid_flex is not None
    assert by_str_uuid_flex.id == session1.id

    by_ident_flex = session_repo.get_by_id_or_identifier("sess_repo_test_01")
    assert by_ident_flex is not None
    assert by_ident_flex.id == session1.id

    assert session_repo.get_by_id_or_identifier("nonexistent_id") is None

    # 6. Active session lookup
    active_sess = session_repo.get_active_session_for_case(case.id)
    assert active_sess is not None
    assert active_sess.id == session1.id

    # 7. List for case
    sessions_list = session_repo.list_for_case(case.id)
    assert len(sessions_list) == 1
    assert sessions_list[0].id == session1.id

    # 8. Update state snapshot
    session_repo.update_snapshot(session1, {"victim_id": "V-SESS-01", "timepoint": 1, "turns": 3})
    refreshed = session_repo.get(session1.id)
    assert refreshed.state_snapshot.get("turns") == 3

    # 9. Close session
    session_repo.close_session(session1)
    closed = session_repo.get(session1.id)
    assert closed.status == SessionStatus.ENDED.value
    assert closed.closed_at is not None

    # Verify no active session remaining
    assert session_repo.get_active_session_for_case(case.id) is None
