"""
Unit and Integration Tests for MEDHA Conversation Manager
=========================================================

Verifies:
1. New session creation & lifecycle
2. Multiple message processing
3. Conversation history preservation
4. State updates & canonical feature tracking
5. Text Engine invocation & continuous probabilities
6. Session isolation between victims/sessions
7. Malformed input handling (types, closed sessions, non-existent sessions)
8. Failed Text Engine call resilience & missingness preservation
9. Pluggable interfaces (Safety Gateway, Question Engine, LLM Provider)
10. End-to-end integration: User message -> ConversationManager -> MedhaState -> MedhaV2Adapter -> predict_v2()
"""

import pytest
from typing import Any, Dict, List, Optional

from chatbot.conversation_manager import (
    ConversationManager,
    ConversationSession,
    TurnResult,
)
from chatbot.state.medha_state import MedhaState, QuestionRecord, TEXT_FEATURES
from chatbot.engines.text_adapter import MedhaTextAdapter, TextEngineResult
from chatbot.interfaces import (
    LLMProviderProtocol,
    LLMResponse,
    PlaceholderLLMProvider,
    SafetyGatewayProtocol,
    SafetyResult,
    PassThroughSafetyGateway,
    QuestionEngineProtocol,
    PassThroughQuestionEngine,
)
from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter


# Helper mock text adapter for fast deterministic unit tests
class MockTextAdapter:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0
        self.last_text: Optional[str] = None

    def process_and_update_state(
        self,
        state: MedhaState,
        text: Optional[str],
        language: Optional[str] = None,
        source: str = "chatbot",
    ) -> TextEngineResult:
        self.call_count += 1
        self.last_text = text

        if self.should_fail:
            raise RuntimeError("Underlying Text Engine failed with CUDA OOM")

        if text is None or not str(text).strip():
            for feat in TEXT_FEATURES:
                state.text_features[feat] = None
            state.set_modality_availability("text", 0.0)
            return TextEngineResult(
                text_available=0.0,
                features={feat: None for feat in TEXT_FEATURES},
                raw_vector=None,
                source=source,
                language=language,
            )

        features = {
            "Text_Distress": 0.6543,
            "Fear": 0.4321,
            "Threat_Context": 0.7890,
            "Negative_Affect": 0.5555,
            "Urgency": 0.3333,
        }
        state.update_features_batch("text", features)
        state.set_modality_availability("text", 1.0)

        return TextEngineResult(
            text_available=1.0,
            features=features,
            raw_vector={"mock": 1.0},
            source=source,
            language=language,
        )


# ===========================================================================
# 1. NEW SESSION LIFECYCLE
# ===========================================================================

def test_new_session():
    """Verifies clean creation of isolated conversation sessions."""
    manager = ConversationManager(text_adapter=MockTextAdapter())

    session = manager.create_session(
        victim_id="victim_alpha",
        session_id="session_001",
        timepoint=1,
        metadata={"channel": "web_chat"},
    )

    assert isinstance(session, ConversationSession)
    assert session.session_id == "session_001"
    assert session.victim_id == "victim_alpha"
    assert session.is_active is True
    assert session.status == "active"
    assert session.metadata["channel"] == "web_chat"

    # State verification
    assert isinstance(session.state, MedhaState)
    assert session.state.victim_id == "victim_alpha"
    assert session.state.session_id == "session_001"
    assert session.state.timepoint == 1

    # Manager registry verification
    assert manager.has_session("session_001") is True
    assert manager.get_session("session_001") is session
    assert manager.get_state("session_001") is session.state
    assert manager.list_sessions() == ["session_001"]

    # Auto-generating session_id when not provided
    session_auto = manager.create_session(victim_id="victim_beta")
    assert session_auto.session_id.startswith("sess_")
    assert manager.has_session(session_auto.session_id) is True
    assert len(manager.list_sessions()) == 2


# ===========================================================================
# 2. MULTIPLE MESSAGES
# ===========================================================================

def test_multiple_messages():
    """Verifies that multiple sequential messages are processed in order."""
    manager = ConversationManager(text_adapter=MockTextAdapter())
    session = manager.create_session(victim_id="victim_002", session_id="sess_multi")

    messages = [
        "Hello, I am having a tough week.",
        "I couldn't sleep because of loud noises outside.",
        "I talked to my sister and felt a bit calmer.",
    ]

    for idx, msg in enumerate(messages, start=1):
        turn_res = manager.process_message(session_id="sess_multi", message=msg)
        assert isinstance(turn_res, TurnResult)
        assert turn_res.session_id == "sess_multi"
        assert turn_res.victim_id == "victim_002"
        assert turn_res.turn_index == idx
        assert turn_res.user_message == msg
        assert len(turn_res.assistant_response) > 0

    # 3 user messages + 3 assistant responses = 6 messages in history
    assert len(session.state.conversation_history) == 6


# ===========================================================================
# 3. HISTORY PRESERVATION
# ===========================================================================

def test_history_preservation():
    """Verifies that conversation history is preserved exactly and in order."""
    manager = ConversationManager(text_adapter=MockTextAdapter())
    session = manager.create_session(victim_id="victim_003", session_id="sess_hist")

    manager.process_message(session_id="sess_hist", message="First message from user")
    manager.process_message(session_id="sess_hist", message="Second message from user")

    history = session.state.conversation_history
    assert len(history) == 4

    assert history[0].role == "user"
    assert history[0].content == "First message from user"
    assert history[1].role == "assistant"

    assert history[2].role == "user"
    assert history[2].content == "Second message from user"
    assert history[3].role == "assistant"

    # Current state pointers
    assert session.state.current_user_message == "Second message from user"
    assert session.state.latest_assistant_response == history[3].content


# ===========================================================================
# 4. STATE UPDATES
# ===========================================================================

def test_state_updates():
    """Verifies that processing a message updates state text features and availability."""
    manager = ConversationManager(text_adapter=MockTextAdapter())
    session = manager.create_session(victim_id="victim_004", session_id="sess_state")

    # Initial state
    assert session.state.text_available is None
    assert all(session.state.text_features[k] is None for k in TEXT_FEATURES)

    # Process message
    turn_res = manager.process_message(session_id="sess_state", message="I feel very unsafe right now.")

    # State after text engine execution
    assert session.state.text_available == 1.0
    for feat in TEXT_FEATURES:
        assert session.state.text_features[feat] is not None
        assert isinstance(session.state.text_features[feat], float)

    # Missing modalities remain missing (not coerced to 0.0)
    assert session.state.voice_available is None
    assert all(session.state.voice_features[k] is None for k in session.state.voice_features)


# ===========================================================================
# 5. TEXT ENGINE INVOCATION
# ===========================================================================

def test_text_engine_invocation():
    """Verifies that the Text Engine adapter is invoked with source='chatbot' and continuous values."""
    mock_adapter = MockTextAdapter()
    manager = ConversationManager(text_adapter=mock_adapter)
    manager.create_session(victim_id="victim_005", session_id="sess_engine")

    user_text = "I heard strange footsteps near my door."
    turn_res = manager.process_message(session_id="sess_engine", message=user_text)

    assert mock_adapter.call_count == 1
    assert mock_adapter.last_text == user_text

    assert turn_res.text_result is not None
    assert turn_res.text_result.text_available == 1.0
    assert turn_res.text_result.source == "chatbot"

    # Continuous values preserved
    assert turn_res.text_result.features["Text_Distress"] == 0.6543
    assert turn_res.text_result.features["Fear"] == 0.4321
    assert turn_res.text_result.features["Threat_Context"] == 0.7890
    assert turn_res.text_result.features["Negative_Affect"] == 0.5555
    assert turn_res.text_result.features["Urgency"] == 0.3333


# ===========================================================================
# 6. SESSION ISOLATION
# ===========================================================================

def test_session_isolation():
    """Verifies that multiple concurrent sessions do not contaminate each other's state."""
    manager = ConversationManager(text_adapter=MockTextAdapter())

    session_a = manager.create_session(victim_id="victim_A", session_id="sess_A")
    session_b = manager.create_session(victim_id="victim_B", session_id="sess_B")

    # Send 2 messages to Session A
    manager.process_message(session_id="sess_A", message="Session A Message 1")
    manager.process_message(session_id="sess_A", message="Session A Message 2")

    # Session B must be completely untouched
    assert len(session_a.state.conversation_history) == 4
    assert len(session_b.state.conversation_history) == 0
    assert session_b.state.current_user_message is None
    assert session_b.state.text_available is None

    # Send 1 message to Session B
    manager.process_message(session_id="sess_B", message="Session B Message 1")

    assert len(session_a.state.conversation_history) == 4
    assert len(session_b.state.conversation_history) == 2
    assert session_a.state.current_user_message == "Session A Message 2"
    assert session_b.state.current_user_message == "Session B Message 1"


# ===========================================================================
# 7. MALFORMED INPUT
# ===========================================================================

def test_malformed_input():
    """Verifies robust validation and error handling for malformed inputs."""
    manager = ConversationManager(text_adapter=MockTextAdapter())
    session = manager.create_session(victim_id="victim_007", session_id="sess_err")

    # Non-string message types must raise TypeError
    with pytest.raises(TypeError, match="Message must be a string"):
        manager.process_message(session_id="sess_err", message=None)  # type: ignore

    with pytest.raises(TypeError, match="Message must be a string"):
        manager.process_message(session_id="sess_err", message=12345)  # type: ignore

    with pytest.raises(TypeError, match="Message must be a string"):
        manager.process_message(session_id="sess_err", message={"text": "hello"})  # type: ignore

    # Non-existent session must raise KeyError
    with pytest.raises(KeyError, match="Session 'unknown_sess' does not exist"):
        manager.process_message(session_id="unknown_sess", message="Hello")

    # Closed session must reject messages with ValueError
    manager.close_session("sess_err")
    with pytest.raises(ValueError, match="Session 'sess_err' is closed"):
        manager.process_message(session_id="sess_err", message="Hello on closed session")

    # Reopening allows messages again
    manager.reopen_session("sess_err")
    turn_res = manager.process_message(session_id="sess_err", message="Hello after reopen")
    assert turn_res.user_message == "Hello after reopen"

    # Empty string or whitespace: handled gracefully without crashing
    turn_blank = manager.process_message(session_id="sess_err", message="   ")
    assert turn_blank.user_message == "   "
    assert turn_blank.text_result.text_available == 0.0
    assert session.state.text_available == 0.0
    # Features remain None (missing)
    assert all(session.state.text_features[f] is None for f in TEXT_FEATURES)

    # Duplicate session creation must raise ValueError
    with pytest.raises(ValueError, match="already exists"):
        manager.create_session(victim_id="victim_other", session_id="sess_err")

    # Invalid victim_id / timepoint
    with pytest.raises(ValueError, match="victim_id"):
        manager.create_session(victim_id="")

    with pytest.raises(ValueError, match="timepoint"):
        manager.create_session(victim_id="vic", timepoint=0)


# ===========================================================================
# 8. FAILED TEXT ENGINE CALL
# ===========================================================================

def test_failed_text_engine_call():
    """Verifies that Text Engine failures are gracefully caught and preserve missingness."""
    # Failing adapter with default raise_on_engine_error=False
    failing_adapter = MockTextAdapter(should_fail=True)
    manager = ConversationManager(
        text_adapter=failing_adapter,
        raise_on_engine_error=False,
    )
    session = manager.create_session(victim_id="victim_008", session_id="sess_fail")

    turn_res = manager.process_message(session_id="sess_fail", message="I feel very scared.")

    # Does not crash the conversational turn
    assert turn_res is not None
    assert len(turn_res.assistant_response) > 0

    # Text availability set to 0.0, error recorded
    assert turn_res.text_result is not None
    assert turn_res.text_result.text_available == 0.0
    assert "CUDA OOM" in str(turn_res.text_result.error_message)

    # State preserves missingness semantics (features remain None, not 0.0)
    assert session.state.text_available == 0.0
    assert all(session.state.text_features[f] is None for f in TEXT_FEATURES)

    # With raise_on_engine_error=True, exception is raised
    strict_manager = ConversationManager(
        text_adapter=failing_adapter,
        raise_on_engine_error=True,
    )
    strict_manager.create_session(victim_id="victim_008b", session_id="sess_strict")
    with pytest.raises(RuntimeError, match="CUDA OOM"):
        strict_manager.process_message(session_id="sess_strict", message="Test strict")


# ===========================================================================
# 9. PLUGGABLE INTERFACES (SAFETY, QUESTION, LLM)
# ===========================================================================

def test_pluggable_interfaces():
    """Verifies clean dependency injection of Safety Gateway, Question Engine, and LLM."""

    # Custom safety gateway that triggers on 'crisis'
    class MockSafetyGateway:
        def evaluate(self, message: str, state: MedhaState, **kwargs):
            if "crisis" in message.lower():
                return SafetyResult(
                    is_triggered=True,
                    category="imminent_danger",
                    crisis_response="EMERGENCY ASSISTANCE: Please call 112 immediately.",
                )
            return SafetyResult(is_triggered=False)

    # Custom question engine that asks about sleep
    class MockQuestionEngine:
        def select_next_question(self, state: MedhaState, **kwargs):
            if len(state.question_history) == 0:
                return QuestionRecord(
                    question_id="Q_SLEEP_01",
                    question_text="How has your sleep been over the past few nights?",
                    intent="assess_sleep_quality",
                )
            return None

    # Custom LLM provider
    class MockLLMProvider:
        def generate_response(self, message: str, state: MedhaState, next_question=None, **kwargs):
            return LLMResponse(
                text=f"Custom empathetic reply. {next_question.question_text if next_question else ''}".strip(),
                metadata={"provider": "mock_custom"},
            )

    manager = ConversationManager(
        text_adapter=MockTextAdapter(),
        safety_gateway=MockSafetyGateway(),
        question_engine=MockQuestionEngine(),
        llm_provider=MockLLMProvider(),
    )

    session = manager.create_session(victim_id="victim_009", session_id="sess_pluggable")

    # Regular message: invokes Question Engine and custom LLM
    turn_1 = manager.process_message(session_id="sess_pluggable", message="Hello there")
    assert "How has your sleep been" in turn_1.assistant_response
    assert turn_1.question_record is not None
    assert turn_1.question_record.question_id == "Q_SLEEP_01"
    assert len(session.state.question_history) == 1

    # Safety trigger: immediate emergency response without question engine
    turn_crisis = manager.process_message(session_id="sess_pluggable", message="I am in crisis and danger")
    assert turn_crisis.safety_result.is_triggered is True
    assert "EMERGENCY ASSISTANCE" in turn_crisis.assistant_response


# ===========================================================================
# 10. END-TO-END V2 PREDICTION INTEGRATION
# ===========================================================================

def test_end_to_end_v2_prediction_integration():
    """
    Validates that a conversation turn processed through ConversationManager
    produces a MedhaState that seamlessly flows into MedhaV2Adapter and
    executes against the frozen MedhaV2Pipeline.predict_v2()!
    """
    from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

    # Use live MedhaTextAdapter
    manager = ConversationManager(text_adapter=MedhaTextAdapter())
    session = manager.create_session(victim_id="victim_e2e", session_id="sess_e2e", timepoint=1)

    # Process conversational message
    turn_res = manager.process_message(
        session_id="sess_e2e",
        message="I have been feeling very anxious and scared since yesterday.",
    )

    assert turn_res.text_result.text_available == 1.0
    assert session.state.text_available == 1.0

    # Prepare DataFrame using V2 Adapter
    adapter = MedhaV2Adapter()
    v2_input_df = adapter.build_input_dataframe(session.state)

    assert len(v2_input_df) == 1
    assert v2_input_df["Victim_ID"].iloc[0] == "victim_e2e"
    assert v2_input_df["Timepoint"].iloc[0] == 1
    assert v2_input_df["Text_Available"].iloc[0] == 1.0
    assert v2_input_df["Voice_Available"].iloc[0] == 0.0

    # Run frozen V2 predictive pipeline directly
    pipeline = MedhaV2Pipeline()
    v2_output = pipeline.predict_v2(v2_input_df)

    assert v2_output is not None
    assert "Fusion_DDS_Prediction" in v2_output.columns
    assert "Struct_Pred" in v2_output.columns
    assert "Text_Pred" in v2_output.columns

    final_dds = v2_output["Fusion_DDS_Prediction"].iloc[0]
    assert 0.0 <= final_dds <= 100.0

    # Also verify high-level adapter.predict(state)
    adapter_res = adapter.predict(session.state)
    assert adapter_res.victim_id == "victim_e2e"
    assert 0.0 <= adapter_res.current_dds <= 100.0
    assert adapter_res.text_available == 1.0
    assert adapter_res.voice_available == 0.0
