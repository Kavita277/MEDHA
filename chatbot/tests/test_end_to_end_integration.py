"""
MEDHA V2 Chatbot: End-to-End Integration Test Suite
===================================================

This suite proves the entire orchestration architecture (Steps 1-12) correctly interfaces
with the frozen MEDHA V2 predictive pipeline without violating engine boundaries.
"""

import os
import sys
import subprocess
from unittest.mock import MagicMock, patch
import pytest

# Add repository root to path so the script can be run directly via python
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from chatbot.conversation_manager import ConversationManager
from chatbot.engines.text_adapter import MedhaTextAdapter
from chatbot.engines.voice_adapter import MedhaVoiceAdapter
from chatbot.engines.behaviour_adapter import MedhaBehaviourAdapter
from chatbot.features.feature_mapper import DeterministicFeatureMapper
from chatbot.safety.safety_gateway import DeterministicSafetyGateway
from chatbot.engines.question_engine import DeterministicQuestionEngine
from chatbot.summary.conversation_summary_engine import ConversationSummaryEngine
from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter, V2PredictionResult
from chatbot.interfaces import LLMProviderProtocol, LLMResponse


class MockLLMProvider(LLMProviderProtocol):
    """Mocks the LLM to avoid real API calls in tests."""
    def __init__(self):
        self.mock_response_text = "I am a mocked response."
        self.mock_observations = []

    def generate_response(self, message, state, next_question=None, **kwargs):
        return LLMResponse(
            text=self.mock_response_text,
            candidate_observations=self.mock_observations,
            metadata={"mocked": True}
        )

    def extract_structured_fields(self, prompt, target_schema, **kwargs):
        return {}


@pytest.fixture
def test_manager():
    """Provides a fully integrated ConversationManager with a mocked LLM."""
    manager = ConversationManager(
        text_adapter=MedhaTextAdapter(),
        llm_provider=MockLLMProvider(),
        safety_gateway=DeterministicSafetyGateway(),
        question_engine=DeterministicQuestionEngine(),
        feature_mapper=DeterministicFeatureMapper(),
        summary_engine=ConversationSummaryEngine(),
        behaviour_adapter=MedhaBehaviourAdapter(),
        voice_adapter=MedhaVoiceAdapter(),
        raise_on_engine_error=False,
    )
    return manager


# ===========================================================================
# 1. Text Only Turn Populates State
# ===========================================================================
def test_1_text_only_turn_populates_state(test_manager):
    session = test_manager.create_session("VIC_TEST_1", "SESS_1")
    
    # Process a text message
    result = test_manager.process_message("SESS_1", "I am feeling very sad today.")
    
    state = result.state
    # Check text adapter extracted features
    assert state.text_available == 1.0
    assert state.text_features["Text_Distress"] is not None
    assert result.assistant_response == test_manager.llm_provider.mock_response_text


# ===========================================================================
# 2. Multi-turn Conversation Accumulates History
# ===========================================================================
def test_2_multi_turn_conversation_accumulates_history(test_manager):
    test_manager.create_session("VIC_TEST_2", "SESS_2")
    
    test_manager.process_message("SESS_2", "Hello")
    test_manager.process_message("SESS_2", "How are you?")
    result = test_manager.process_message("SESS_2", "I need some help.")
    
    state = result.state
    # 3 user messages + 3 assistant responses = 6 history items
    assert len(state.conversation_history) == 6
    assert state.conversation_history[0].role == "user"
    assert state.conversation_history[1].role == "assistant"


# ===========================================================================
# 3. Safety Gateway Triggers on Threat
# ===========================================================================
def test_3_safety_gateway_triggers_on_threat(test_manager):
    session = test_manager.create_session("VIC_TEST_3", "SESS_3")
    
    # Pre-inject a candidate observation to simulate extraction from a previous turn
    # because the safety gateway evaluates the state *before* the LLM extraction in the current turn.
    session.state.add_candidate_observation(domain="safety", semantic_value="unsafe", evidence="I feel unsafe at home", status="candidate")
    
    result = test_manager.process_message("SESS_3", "Please help.")
    
    assert result.safety_result is not None
    assert result.safety_result.is_triggered is True
    assert "crisis helpline" in result.assistant_response.lower()


# ===========================================================================
# 4. Behaviour Data Populates State
# ===========================================================================
def test_4_behaviour_data_populates_state(test_manager):
    test_manager.create_session("VIC_TEST_4", "SESS_4")
    
    behaviour_data = {
        "Session_Duration_Minutes": 5.5,
        "Interaction_Frequency_7d": 1.0,
        "Response_Delay_Hours": 0.0
    }
    
    result = test_manager.process_message("SESS_4", "Hi", behaviour_data=behaviour_data)
    
    state = result.state
    assert state.behav_available == 1.0
    assert state.behaviour_features["Session_Duration_Minutes"] == 5.5
    assert state.behaviour_features["Interaction_Frequency_7d"] == 1.0


# ===========================================================================
# 5. Voice Adapter Sets Unavailable When No Audio
# ===========================================================================
def test_5_voice_adapter_sets_unavailable_when_no_audio(test_manager):
    test_manager.create_session("VIC_TEST_5", "SESS_5")
    
    result = test_manager.process_message("SESS_5", "Hi", audio_path=None)
    
    state = result.state
    # If no audio is provided, voice_available remains None (which the V2 adapter casts to 0.0)
    assert state.voice_available in [0.0, None]
    assert state.voice_features.get("Voice_Distress") is None


# ===========================================================================
# 6. V2 Adapter Predict with Populated State
# ===========================================================================
def test_6_v2_adapter_predict_with_populated_state(test_manager):
    session = test_manager.create_session("VIC_TEST_6", "SESS_6")
    
    # Process text
    test_manager.process_message("SESS_6", "I'm extremely anxious.")
    
    # Process behavior
    test_manager.process_message("SESS_6", "Yes", behaviour_data={"Session_Duration_Minutes": 10.0})
    
    # Simulate some structured feature data for baseline inference
    state = test_manager.get_state("SESS_6")
    state.update_feature("structured", "Mood", 2.0)
    state.update_feature("structured", "Stress", 4.0)
    
    # Call frozen engine V2
    v2_adapter = MedhaV2Adapter(enable_triage=True)
    prediction = v2_adapter.predict(state)
    
    assert isinstance(prediction, V2PredictionResult)
    assert 0.0 <= prediction.current_dds <= 100.0


# ===========================================================================
# 7. V2 Adapter Text Only State
# ===========================================================================
def test_7_v2_adapter_text_only_state(test_manager):
    test_manager.create_session("VIC_TEST_7", "SESS_7")
    
    test_manager.process_message("SESS_7", "I'm just chatting via text today.")
    
    state = test_manager.get_state("SESS_7")
    v2_adapter = MedhaV2Adapter(enable_triage=False)
    prediction = v2_adapter.predict(state)
    
    assert prediction.voice_available == 0.0
    assert prediction.text_available == 1.0
    assert 0.0 <= prediction.current_dds <= 100.0


# ===========================================================================
# 8. Summary Engine Integration
# ===========================================================================
@patch("chatbot.summary.conversation_summary_engine.ConversationSummaryEngine._parse_json_from_llm")
def test_8_summary_engine_integration(mock_parse, test_manager):
    # Mock the LLM to return valid JSON payload
    mock_parse.return_value = {
        "important_facts": [{"content": "User has a new job"}],
        "current_concerns": [],
        "recent_events": [],
        "support_context": [],
        "preferences": [],
        "ongoing_topics": [],
        "unresolved_topics": [],
        "important_observations": []
    }
    
    test_manager.create_session("VIC_TEST_8", "SESS_8")
    test_manager.process_message("SESS_8", "I got a new job recently.")
    
    state = test_manager.get_state("SESS_8")
    summary = state.conversation_summary
    
    assert len(summary.important_facts) > 0
    assert summary.important_facts[0].content == "User has a new job"


# ===========================================================================
# 9. Question Engine Selects Question
# ===========================================================================
def test_9_question_engine_selects_question(test_manager):
    test_manager.create_session("VIC_TEST_9", "SESS_9")
    
    result = test_manager.process_message("SESS_9", "Hello")
    
    # Assuming "Safety" is the first missing core feature
    assert result.question_record is not None
    assert result.question_record.question_id is not None


# ===========================================================================
# 10. Feature Mapper Maps Threat Event
# ===========================================================================
def test_10_feature_mapper_maps_threat_event(test_manager):
    test_manager.create_session("VIC_TEST_10", "SESS_10")
    
    test_manager.llm_provider.mock_observations = [
        {"domain": "threat_event", "value": "present", "evidence": "someone threatened me"}
    ]
    
    result = test_manager.process_message("SESS_10", "Someone threatened me.")
    
    state = result.state
    assert state.structured_features["Threat_Event"] == 1.0


# ===========================================================================
# 11. Frozen Engine File Integrity
# ===========================================================================
def test_11_frozen_engine_file_integrity():
    """Verify that NO files inside engine/ have been modified."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Run git status on engine directory
    result = subprocess.run(["git", "status", "--short", "engine/"], capture_output=True, text=True, cwd=repo_root)
    
    # The output should be completely empty if there are no modifications
    assert result.stdout.strip() == "", f"Found modified files in engine/: {result.stdout}"


# ===========================================================================
# 12. Full Pipeline Text to Prediction
# ===========================================================================
def test_12_full_pipeline_text_to_prediction(test_manager):
    session = test_manager.create_session("VIC_TEST_12", "SESS_12")
    
    # Multi-turn interaction
    test_manager.process_message("SESS_12", "Hello")
    test_manager.process_message("SESS_12", "I am feeling a little anxious but okay.", behaviour_data={"Session_Duration_Minutes": 3.0})
    test_manager.process_message("SESS_12", "I have some things to deal with.")
    
    state = test_manager.get_state("SESS_12")
    v2_adapter = MedhaV2Adapter(enable_triage=True)
    
    # Final ML Prediction (should be fully deterministic ML execution)
    prediction = v2_adapter.predict(state)
    
    assert prediction.victim_id == "VIC_TEST_12"
    assert prediction.timepoint == 1
    assert 0.0 <= prediction.current_dds <= 100.0
    assert prediction.text_available == 1.0
    assert prediction.behav_available == 1.0
