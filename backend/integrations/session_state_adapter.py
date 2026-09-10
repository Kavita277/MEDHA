"""
Session State Integration Adapter
=================================

Bridges persistent backend database sessions (PostgreSQL) with the runtime
in-memory MedhaState and ConversationManager without modifying the frozen
chatbot/ state or engine layers.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional, TYPE_CHECKING

from chatbot.state.medha_state import MedhaState
from chatbot.conversation_manager import ConversationSession, ConversationManager

if TYPE_CHECKING:
    from backend.persistence.models.session import SessionModel


def serialize_medha_state(state: MedhaState) -> Dict[str, Any]:
    """
    Serializes an in-memory MedhaState into a pure Python dictionary
    suitable for JSON/JSONB storage in PostgreSQL.
    """
    return state.to_dict()


def restore_medha_state(snapshot: Dict[str, Any]) -> MedhaState:
    """
    Reconstitutes a fully functional in-memory MedhaState instance from
    a stored dictionary snapshot.
    """
    return MedhaState.from_dict(snapshot)


def create_initial_medha_state(
    victim_id: str,
    session_id: str,
    timepoint: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> MedhaState:
    """
    Initializes a fresh, clean MedhaState container for a new session.
    """
    return MedhaState(
        victim_id=victim_id,
        session_id=session_id,
        timepoint=timepoint,
        metadata=metadata,
    )


def restore_conversation_session(session_model: SessionModel) -> ConversationSession:
    """
    Builds a runtime ConversationSession from a persistent database SessionModel.
    Restores the runtime MedhaState from state_snapshot if present; otherwise
    initializes a fresh MedhaState.
    """
    victim_id = session_model.case.victim_id if session_model.case else "UNKNOWN"

    if session_model.state_snapshot:
        state = restore_medha_state(session_model.state_snapshot)
    else:
        state = create_initial_medha_state(
            victim_id=victim_id,
            session_id=session_model.session_identifier,
            timepoint=session_model.timepoint,
        )

    # Runtime status convention in ConversationManager is "active" or "closed"
    runtime_status = "active" if session_model.status == "ACTIVE" else "closed"

    return ConversationSession(
        session_id=session_model.session_identifier,
        victim_id=victim_id,
        state=state,
        status=runtime_status,
        created_at=session_model.created_at.isoformat() if session_model.created_at else "",
        updated_at=session_model.updated_at.isoformat() if session_model.updated_at else "",
        metadata=copy.deepcopy(state.metadata),
    )


def attach_to_conversation_manager(
    manager: ConversationManager,
    session_model: SessionModel,
) -> ConversationSession:
    """
    Restores and mounts a persistent database session into a ConversationManager instance's
    active session registry.
    """
    conv_session = restore_conversation_session(session_model)
    manager._sessions[session_model.session_identifier] = conv_session
    return conv_session


def sync_from_conversation_manager(
    manager: ConversationManager,
    session_model: SessionModel,
) -> Dict[str, Any]:
    """
    Extracts the latest state dictionary from ConversationManager for persistence.
    """
    sid = session_model.session_identifier
    if sid not in manager._sessions:
        raise KeyError(f"Session '{sid}' is not registered in the ConversationManager.")

    conv_session = manager._sessions[sid]
    return conv_session.state.to_dict()
