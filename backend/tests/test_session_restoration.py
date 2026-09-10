"""
Session State Restoration Tests
===============================

Verifies lossless round-trip serialization, database snapshot persistence,
and runtime reconstitution of MedhaState and ConversationSession.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.integrations.session_state_adapter import (
    attach_to_conversation_manager,
    create_initial_medha_state,
    restore_conversation_session,
    restore_medha_state,
    serialize_medha_state,
    sync_from_conversation_manager,
)
from backend.persistence.base import Base
from backend.persistence.database import build_engine
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.persistence.repositories.user import UserRepository
from chatbot.conversation_manager import ConversationManager
from chatbot.state.medha_state import MedhaState


@pytest.fixture
def db_session():
    """Provides an isolated transactional SQLite session."""
    settings = Settings(DATABASE_URL="sqlite:///:memory:", DB_ECHO=False)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_medha_state_serialization_round_trip():
    """Verifies that an in-memory MedhaState with rich content survives serialization roundtrip."""
    state = MedhaState(
        victim_id="V-RESTORE-001",
        session_id="sess_roundtrip_01",
        timepoint=2,
    )

    # 1. Add conversation turns
    state.add_user_message("I have been feeling quite anxious lately.")
    state.add_assistant_response("I hear you. Could you share what has been on your mind?")

    # 2. Add question history
    state.record_question_asked(
        question_id="Q-MOOD-01",
        question_text="How would you rate your mood today on a scale of 1-10?",
        intent="mood_assessment",
    )
    state.record_question_answered(
        question_id="Q-MOOD-01",
        response_text="Around a 4.",
    )

    # 3. Add observations and features
    state.add_candidate_observation(domain="mood", semantic_value="low", evidence="Around a 4.")
    state.update_feature("structured", "Mood", 4.0)
    state.update_feature("structured", "Stress", 7.5)
    state.update_feature("text", "Text_Distress", 0.65)
    state.set_modality_availability("text", 1.0)
    state.set_modality_availability("voice", 0.0)

    # 4. Serialize
    snapshot = serialize_medha_state(state)
    assert isinstance(snapshot, dict)
    assert snapshot["victim_id"] == "V-RESTORE-001"
    assert snapshot["timepoint"] == 2
    assert len(snapshot["conversation_history"]) == 2
    assert len(snapshot["question_history"]) == 1

    # 5. Restore
    restored = restore_medha_state(snapshot)
    assert restored.victim_id == "V-RESTORE-001"
    assert restored.session_id == "sess_roundtrip_01"
    assert restored.timepoint == 2
    assert len(restored.conversation_history) == 2
    assert restored.conversation_history[0].role == "user"
    assert restored.conversation_history[0].content == "I have been feeling quite anxious lately."
    assert restored.conversation_history[1].role == "assistant"
    assert restored.conversation_history[1].content == "I hear you. Could you share what has been on your mind?"
    assert restored.structured_features["Mood"] == 4.0
    assert restored.structured_features["Stress"] == 7.5
    assert restored.text_features["Text_Distress"] == 0.65
    assert restored.text_available == 1.0
    assert restored.voice_available == 0.0
    assert len(restored.candidate_observations) == 1
    assert restored.candidate_observations[0].semantic_value == "low"


def test_session_model_database_restoration(db_session: Session):
    """Verifies restoring runtime MedhaState and ConversationSession from persistent database records."""
    user_repo = UserRepository(db_session)
    therapist_repo = TherapistRepository(db_session)
    case_repo = CaseRepository(db_session)
    session_repo = SessionRepository(db_session)

    # 1. Setup Patient, Therapist, Case
    patient = user_repo.add(User(name="Restore Patient", email="rp@example.com", role=UserRole.USER, password_hash="h"))
    t_user = user_repo.add(User(name="Restore Therapist", email="rt@example.com", role=UserRole.THERAPIST, password_hash="h"))
    therapist = therapist_repo.add(Therapist(user_id=t_user.id, display_name="Dr. Restore"))
    case = case_repo.add(Case(victim_id="V-RESTORE-DB", user_id=patient.id, therapist_id=therapist.id, current_timepoint=3))

    # 2. Create initial state and persist session
    initial_state = create_initial_medha_state(
        victim_id=case.victim_id,
        session_id="sess_db_restore_01",
        timepoint=case.current_timepoint,
    )
    initial_state.add_user_message("Hello MEDHA.")
    initial_state.add_assistant_response("Hello, I am MEDHA. How can I support you today?")

    session_record = SessionModel(
        id=uuid.uuid4(),
        case_id=case.id,
        session_identifier="sess_db_restore_01",
        timepoint=3,
        status=SessionStatus.ACTIVE.value,
        state_snapshot=serialize_medha_state(initial_state),
    )
    session_repo.add(session_record)

    # 3. Retrieve from DB and restore ConversationSession
    fetched = session_repo.get_by_identifier("sess_db_restore_01")
    assert fetched is not None
    conv_session = restore_conversation_session(fetched)

    assert conv_session.session_id == "sess_db_restore_01"
    assert conv_session.victim_id == "V-RESTORE-DB"
    assert conv_session.is_active is True
    assert len(conv_session.state.conversation_history) == 2

    # 4. Attach to ConversationManager and perform conversation turns
    manager = ConversationManager()
    attach_to_conversation_manager(manager, fetched)
    assert "sess_db_restore_01" in manager._sessions

    # Mutate through conversation manager
    manager._sessions["sess_db_restore_01"].state.add_user_message("Let us continue our session.")
    
    # Sync back to DB
    updated_snapshot = sync_from_conversation_manager(manager, fetched)
    session_repo.update_snapshot(fetched, updated_snapshot)

    # Verify updated DB state
    reloaded = session_repo.get(fetched.id)
    assert len(reloaded.state_snapshot["conversation_history"]) == 3
    assert reloaded.state_snapshot["conversation_history"][2]["content"] == "Let us continue our session."
