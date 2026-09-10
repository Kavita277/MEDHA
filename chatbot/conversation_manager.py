"""
MEDHA Conversation Manager
==========================

Central orchestration layer coordinating:
- Session lifecycle (creation, tracking, isolation, closing)
- Conversation history & turn recording
- Question history
- Central MedhaState
- Text Engine Adapter (extracting canonical V2 text features)
- Pluggable downstream interfaces (LLM, Question Engine, Feature Mapper, Safety Gateway)

ABSOLUTE ARCHITECTURAL CONSTRAINTS:
The Conversation Manager must NOT itself:
- Calculate DDS
- Calculate future risk
- Diagnose
- Select or fabricate numerical risk scores
- Implement fusion models
- Implement feature mapping logic
- Implement safety risk scoring
All predictive modeling and clinical inference remain the strict responsibility of MEDHA V2.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from chatbot.state.medha_state import MedhaState, QuestionRecord, TEXT_FEATURES
from chatbot.engines.text_adapter import MedhaTextAdapter, TextEngineResult
from chatbot.features.feature_mapper import DeterministicFeatureMapper
from chatbot.engines.question_engine import DeterministicQuestionEngine
from chatbot.safety.safety_gateway import DeterministicSafetyGateway
from chatbot.summary.conversation_summary_engine import ConversationSummaryEngine
from chatbot.interfaces import (
    LLMProviderProtocol,
    LLMResponse,
    PlaceholderLLMProvider,
    SafetyGatewayProtocol,
    SafetyResult,
    PassThroughSafetyGateway,
    QuestionEngineProtocol,
    PassThroughQuestionEngine,
    FeatureMapperProtocol,
    PassThroughFeatureMapper,
    TextAdapterProtocol,
    SummaryEngineProtocol,
    PassThroughSummaryEngine,
    BehaviourAdapterProtocol,
    PassThroughBehaviourAdapter,
    VoiceAdapterProtocol,
    PassThroughVoiceAdapter,
)


def _current_iso_timestamp() -> str:
    """Returns current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# ===========================================================================
# SESSION & TURN DATA STRUCTURES
# ===========================================================================

@dataclass
class ConversationSession:
    """
    Encapsulates an active or historical conversation session with its MedhaState.
    """
    session_id: str
    victim_id: str
    state: MedhaState
    status: str = "active"  # "active" or "closed"
    created_at: str = field(default_factory=_current_iso_timestamp)
    updated_at: str = field(default_factory=_current_iso_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def close(self) -> None:
        self.status = "closed"
        self.updated_at = _current_iso_timestamp()

    def reopen(self) -> None:
        self.status = "active"
        self.updated_at = _current_iso_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": copy.deepcopy(self.metadata),
            "state": self.state.to_dict(),
        }


@dataclass
class TurnResult:
    """
    Comprehensive record of a completed conversation turn.
    Exposes conversational responses and state without exposing raw clinical scores.
    """
    session_id: str
    victim_id: str
    turn_index: int
    user_message: str
    assistant_response: str
    state: MedhaState
    text_result: Optional[TextEngineResult] = None
    safety_result: Optional[SafetyResult] = None
    question_record: Optional[QuestionRecord] = None
    timestamp: str = field(default_factory=_current_iso_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "turn_index": self.turn_index,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "text_result": self.text_result.to_dict() if self.text_result else None,
            "safety_result": {
                "is_triggered": self.safety_result.is_triggered,
                "category": self.safety_result.category,
            } if self.safety_result else None,
            "question_record": self.question_record.to_dict() if self.question_record else None,
            "timestamp": self.timestamp,
            "metadata": copy.deepcopy(self.metadata),
        }


# ===========================================================================
# CONVERSATION MANAGER
# ===========================================================================

class ConversationManager:
    """
    Central orchestration layer coordinating conversation flow, session lifecycle,
    and state updates before passing verified information to MEDHA V2.
    """

    def __init__(
        self,
        text_adapter: Optional[TextAdapterProtocol] = None,
        llm_provider: Optional[LLMProviderProtocol] = None,
        safety_gateway: Optional[SafetyGatewayProtocol] = None,
        question_engine: Optional[QuestionEngineProtocol] = None,
        feature_mapper: Optional[FeatureMapperProtocol] = None,
        summary_engine: Optional[SummaryEngineProtocol] = None,
        behaviour_adapter: Optional[BehaviourAdapterProtocol] = None,
        voice_adapter: Optional[VoiceAdapterProtocol] = None,
        safety_trigger: Optional[Any] = None,
        raise_on_engine_error: bool = False,
    ):
        """
        Initializes the Conversation Manager with pluggable dependencies.

        Parameters
        ----------
        text_adapter : Optional[TextAdapterProtocol]
            Adapter interfacing with the existing frozen Text Engine.
            Defaults to MedhaTextAdapter().
        llm_provider : Optional[LLMProviderProtocol]
            Pluggable LLM response generator. Defaults to PlaceholderLLMProvider().
        safety_gateway : Optional[SafetyGatewayProtocol]
            Pluggable safety evaluator. Defaults to PassThroughSafetyGateway().
        question_engine : Optional[QuestionEngineProtocol]
            Pluggable controlled question engine. Defaults to PassThroughQuestionEngine().
        feature_mapper : Optional[FeatureMapperProtocol]
            Pluggable observation mapper. Defaults to PassThroughFeatureMapper().
        summary_engine : Optional[SummaryEngineProtocol]
            Pluggable summary generator. Defaults to ConversationSummaryEngine().
        behaviour_adapter : Optional[BehaviourAdapterProtocol]
            Pluggable behaviour adapter.
        voice_adapter : Optional[VoiceAdapterProtocol]
            Pluggable voice adapter.
        safety_trigger: Optional[Any]
            The new non-blocking safety trigger evaluating every message.
        raise_on_engine_error : bool
            If True, errors in specialist engines propagate as exceptions.
            If False, falls back safely to missingness semantics (availability=0.0).
        """
        self.text_adapter: TextAdapterProtocol = text_adapter or MedhaTextAdapter()
        self.llm_provider: LLMProviderProtocol = llm_provider or PlaceholderLLMProvider()
        self.safety_gateway: SafetyGatewayProtocol = safety_gateway or DeterministicSafetyGateway()
        self.question_engine: QuestionEngineProtocol = question_engine or DeterministicQuestionEngine()
        self.feature_mapper: FeatureMapperProtocol = feature_mapper or DeterministicFeatureMapper()
        self.summary_engine: SummaryEngineProtocol = summary_engine or ConversationSummaryEngine()
        
        if safety_trigger is None:
            try:
                from chatbot.safety.safety_trigger import SafetyTrigger
                self.safety_trigger = SafetyTrigger()
            except ImportError:
                self.safety_trigger = None
        else:
            self.safety_trigger = safety_trigger
        
        if behaviour_adapter is None:
            try:
                from chatbot.engines.behaviour_adapter import MedhaBehaviourAdapter
                self.behaviour_adapter = MedhaBehaviourAdapter()
            except ImportError:
                self.behaviour_adapter = PassThroughBehaviourAdapter()
        else:
            self.behaviour_adapter = behaviour_adapter

        if voice_adapter is None:
            try:
                from chatbot.engines.voice_adapter import MedhaVoiceAdapter
                self.voice_adapter = MedhaVoiceAdapter()
            except ImportError:
                self.voice_adapter = PassThroughVoiceAdapter()
        else:
            self.voice_adapter = voice_adapter
            
        self.raise_on_engine_error: bool = raise_on_engine_error

        # In-memory session registry (indexed by session_id)
        self._sessions: Dict[str, ConversationSession] = {}

    # -----------------------------------------------------------------------
    # Session Lifecycle Management
    # -----------------------------------------------------------------------

    def create_session(
        self,
        victim_id: str,
        session_id: Optional[str] = None,
        timepoint: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationSession:
        """
        Creates and registers a new isolated conversation session.

        Parameters
        ----------
        victim_id : str
            Victim identifier.
        session_id : Optional[str]
            Optional custom session identifier. If None, a unique ID is generated.
        timepoint : int
            Session timepoint index (>= 1).
        metadata : Optional[Dict[str, Any]]
            Optional session metadata.

        Returns
        -------
        ConversationSession
            The newly created session.
        """
        if not isinstance(victim_id, str) or not victim_id.strip():
            raise ValueError("victim_id must be a non-empty string.")

        if not isinstance(timepoint, int) or timepoint < 1:
            raise ValueError(f"timepoint must be a positive integer >= 1, got {timepoint}.")

        sid = session_id.strip() if session_id and session_id.strip() else f"sess_{uuid.uuid4().hex[:12]}"

        if sid in self._sessions:
            raise ValueError(f"Session with ID '{sid}' already exists.")

        # Initialize fresh, isolated MedhaState
        state = MedhaState(
            victim_id=victim_id.strip(),
            session_id=sid,
            timepoint=timepoint,
            metadata=metadata,
        )

        session = ConversationSession(
            session_id=sid,
            victim_id=victim_id.strip(),
            state=state,
            status="active",
            metadata=copy.deepcopy(metadata or {}),
        )

        self._sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> ConversationSession:
        """Retrieves an existing session by ID, or raises KeyError if not found."""
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id must be a non-empty string.")

        sid = session_id.strip()
        if sid not in self._sessions:
            raise KeyError(f"Session '{sid}' does not exist.")
        return self._sessions[sid]

    def get_or_create_session(
        self,
        victim_id: str,
        session_id: Optional[str] = None,
        timepoint: int = 1,
    ) -> ConversationSession:
        """Retrieves existing session or creates a new one if not present."""
        if session_id and session_id.strip() in self._sessions:
            session = self._sessions[session_id.strip()]
            if session.victim_id != victim_id.strip():
                raise ValueError(
                    f"Session '{session_id}' belongs to victim '{session.victim_id}', "
                    f"not '{victim_id}'."
                )
            return session
        return self.create_session(victim_id=victim_id, session_id=session_id, timepoint=timepoint)

    def close_session(self, session_id: str) -> ConversationSession:
        """Closes an existing session."""
        session = self.get_session(session_id)
        session.close()
        return session

    def reopen_session(self, session_id: str) -> ConversationSession:
        """Reopens a closed session."""
        session = self.get_session(session_id)
        session.reopen()
        return session

    def delete_session(self, session_id: str) -> None:
        """Removes a session from memory."""
        sid = session_id.strip() if isinstance(session_id, str) else session_id
        if sid in self._sessions:
            del self._sessions[sid]

    def list_sessions(self) -> List[str]:
        """Returns all registered session IDs."""
        return list(self._sessions.keys())

    def has_session(self, session_id: str) -> bool:
        """Returns True if session_id is currently registered."""
        return isinstance(session_id, str) and session_id.strip() in self._sessions

    def get_state(self, session_id: str) -> MedhaState:
        """Convenience method to retrieve a session's current MedhaState."""
        return self.get_session(session_id).state

    # -----------------------------------------------------------------------
    # Message Processing & Turn Orchestration
    # -----------------------------------------------------------------------

    def process_message(
        self,
        session_id: str,
        message: str,
        language: Optional[str] = None,
        behaviour_data: Optional[Dict[str, Any]] = None,
        audio_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TurnResult:
        """
        Processes a user message through the orchestration pipeline:
        1. Validates session existence and status.
        2. Records user message in MedhaState.
        3. Invokes Safety Gateway (immediate crisis intervention if triggered).
        4. Invokes existing Text Engine via adapter (updates state text features).
        5. Invokes Question Engine (selects next question if appropriate).
        6. Invokes LLM Provider (generates natural, supportive response).
        7. Records assistant response and returns TurnResult.

        Parameters
        ----------
        session_id : str
            Active session identifier.
        message : str
            User input text.
        language : Optional[str]
            Optional language hint ('en', 'hi', 'hinglish').
        metadata : Optional[Dict[str, Any]]
            Optional per-turn metadata.

        Returns
        -------
        TurnResult
            Comprehensive record of the turn.
        """
        # 1. Validation
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id must be a non-empty string.")

        session = self.get_session(session_id)

        if not session.is_active:
            raise ValueError(f"Session '{session.session_id}' is closed. Reopen before sending messages.")

        if not isinstance(message, str):
            raise TypeError(f"Message must be a string, got {type(message).__name__}.")

        state = session.state
        turn_metadata = copy.deepcopy(metadata or {})

        # 2. Record User Message in MedhaState
        state.add_user_message(content=message, metadata=turn_metadata)
        turn_index = (len(state.conversation_history) + 1) // 2

        # 2a. Safety Trigger (Additive, Non-Blocking, Alerts backend)
        if hasattr(self, 'safety_trigger') and self.safety_trigger is not None:
            try:
                self.safety_trigger.evaluate(
                    message=message,
                    state=state,
                    llm_provider=self.llm_provider
                )
            except Exception as e:
                # Do not block MEDHA pipeline on safety trigger failure
                pass

        # 2b. Behaviour Engine Adapter Hook
        if behaviour_data is not None:
            self.behaviour_adapter.process_and_update_state(state, behaviour_data)

        # 2c. Voice Engine Adapter Hook (processes raw audio -> Voice features)
        self.voice_adapter.process_and_update_state(state, audio_path)

        # 3. Safety Gateway Hook (Replaceable)
        safety_res = self.safety_gateway.evaluate(message=message, state=state)
        if safety_res.is_triggered:
            # Deterministic immediate safety routing
            crisis_text = (
                safety_res.crisis_response
                or "I hear you, and your safety is the highest priority. "
                   "Please connect immediately with a crisis helpline or a trusted professional."
            )
            state.add_assistant_response(
                content=crisis_text,
                metadata={"safety_triggered": True, "category": safety_res.category},
            )
            session.updated_at = _current_iso_timestamp()
            return TurnResult(
                session_id=session.session_id,
                victim_id=session.victim_id,
                turn_index=turn_index,
                user_message=message,
                assistant_response=crisis_text,
                state=state,
                text_result=None,
                safety_result=safety_res,
                question_record=None,
                metadata=turn_metadata,
            )

        # 4. Text Engine Adapter (Frozen MuRIL multi-head continuous inference)
        text_result: Optional[TextEngineResult] = None
        try:
            text_result = self.text_adapter.process_and_update_state(
                state=state,
                text=message,
                language=language,
                source="chatbot",
            )
        except Exception as e:
            if self.raise_on_engine_error:
                raise
            # Safe missingness fallback: text_available = 0.0, features remain None
            for feat in TEXT_FEATURES:
                state.text_features[feat] = None
            state.set_modality_availability("text", 0.0)
            text_result = TextEngineResult(
                text_available=0.0,
                features={feat: None for feat in TEXT_FEATURES},
                raw_vector=None,
                source="chatbot",
                language=language,
                error_message=str(e),
            )

        # 5. Feature Mapper Hook moved to step 7c (after LLM observation extraction)

        # 6. Question Engine Hook (Replaceable)
        next_question: Optional[QuestionRecord] = self.question_engine.select_next_question(
            state=state
        )
        if next_question:
            state.record_question_asked(
                question_id=next_question.question_id,
                question_text=next_question.question_text,
                intent=next_question.intent,
                cooldown_until=next_question.cooldown_until,
                metadata=next_question.metadata,
            )

        # 6.5. Summary Engine Hook
        try:
            self.summary_engine.update_summary(state=state, llm_provider=self.llm_provider)
        except Exception as e:
            if self.raise_on_engine_error:
                raise
            import logging
            logging.getLogger(__name__).error(f"Summary engine failed: {e}")

        # 7. LLM Provider Hook (Replaceable response pipeline)
        llm_res: LLMResponse = self.llm_provider.generate_response(
            message=message,
            state=state,
            next_question=next_question,
        )

        # 7b. Store LLM-extracted candidate observations in MedhaState
        #     These remain qualitative observations, NOT V2 numeric features.
        #     Step 6 (Feature Mapper) will handle authoritative mapping.
        if llm_res.candidate_observations:
            for obs in llm_res.candidate_observations:
                if isinstance(obs, dict) and obs.get("domain") and obs.get("evidence"):
                    state.add_candidate_observation(
                        domain=obs["domain"],
                        semantic_value=obs.get("value"),
                        evidence=obs.get("evidence"),
                        status="candidate",
                    )

            # 7c. Feature Mapper Hook (Replaceable) — now with observations
            self.feature_mapper.process_observations(
                state=state,
                candidate_observations=llm_res.candidate_observations,
            )

        # Record assistant reply in MedhaState
        state.add_assistant_response(
            content=llm_res.text,
            metadata=llm_res.metadata,
        )

        session.updated_at = _current_iso_timestamp()

        # 8. Return TurnResult
        return TurnResult(
            session_id=session.session_id,
            victim_id=session.victim_id,
            turn_index=turn_index,
            user_message=message,
            assistant_response=llm_res.text,
            state=state,
            text_result=text_result,
            safety_result=safety_res,
            question_record=next_question,
            metadata=turn_metadata,
        )
