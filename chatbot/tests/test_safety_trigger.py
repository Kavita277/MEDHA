"""
Tests for the Safety Trigger integration (MEDHA V2 Chatbot).
Verifies that explicit immediate safety concerns trigger backend alerts
without blocking the main predictive pipeline.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add repository root to path so the script can be run directly via python
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from chatbot.state.medha_state import MedhaState
from chatbot.conversation_manager import ConversationManager
from chatbot.safety.safety_trigger import SafetyTrigger, MockAlertEngine
from chatbot.interfaces import LLMProviderProtocol, LLMResponse


class MockClassifyingLLMProvider(LLMProviderProtocol):
    """Mocks the LLM provider to return deterministic safety classifications."""
    def __init__(self):
        self.classification_result = None

    def generate_response(self, message, state, next_question=None, **kwargs):
        return LLMResponse(text="Mock response", candidate_observations=[], metadata={})

    def extract_structured_fields(self, prompt, target_schema, **kwargs):
        return self.classification_result


@pytest.fixture
def mock_llm():
    return MockClassifyingLLMProvider()


@pytest.fixture
def alert_engine():
    return MockAlertEngine()


@pytest.fixture
def safety_trigger(alert_engine):
    return SafetyTrigger(alert_engine=alert_engine)


@pytest.fixture
def test_manager(mock_llm, safety_trigger):
    manager = ConversationManager(llm_provider=mock_llm, safety_trigger=safety_trigger)
    return manager


# =====================================================================
# REQUIRED TESTS (1-16)
# =====================================================================

def test_1_explicit_current_danger(safety_trigger, mock_llm, alert_engine):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "immediate_danger",
        "evidence": "I am in danger right now."
    }
    event = safety_trigger.evaluate("I am in danger right now.", state, mock_llm)
    assert event is not None
    assert event.trigger_type == "immediate_danger"
    assert len(alert_engine.emitted_events) == 1


def test_2_explicit_suicidal_intent(safety_trigger, mock_llm, alert_engine):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "suicidal_intent",
        "evidence": "I am going to kill myself tonight."
    }
    event = safety_trigger.evaluate("I am going to kill myself tonight.", state, mock_llm)
    assert event.trigger_type == "suicidal_intent"
    assert len(alert_engine.emitted_events) == 1


def test_3_explicit_self_harm_intent(safety_trigger, mock_llm, alert_engine):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "self_harm_intent",
        "evidence": "I want to cut myself."
    }
    event = safety_trigger.evaluate("I want to cut myself.", state, mock_llm)
    assert event.trigger_type == "self_harm_intent"


def test_4_explicit_imminent_threat_to_another(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "threat_to_other",
    }
    event = safety_trigger.evaluate("I am going to hurt him.", state, mock_llm)
    assert event.trigger_type == "threat_to_other"


def test_5_immediate_protection_concern(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "immediate_protection_concern",
    }
    event = safety_trigger.evaluate("He is hitting my child right now.", state, mock_llm)
    assert event.trigger_type == "immediate_protection_concern"


def test_6_normal_sadness(safety_trigger, mock_llm, alert_engine):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I am so sad today.", state, mock_llm)
    assert event is None
    assert len(alert_engine.emitted_events) == 0


def test_7_normal_stress(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I am stressed about my exams.", state, mock_llm)
    assert event is None


def test_8_anger_without_threat(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I am so angry at my boss.", state, mock_llm)
    assert event is None


def test_9_negated_suicidal_statement(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I am not suicidal.", state, mock_llm)
    assert event is None


def test_10_negated_threat_statement(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I don't want to hurt anyone.", state, mock_llm)
    assert event is None


def test_11_historical_safety_event(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I was in danger last year.", state, mock_llm)
    assert event is None


def test_12_contextual_mention(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {"safety_trigger": False}
    event = safety_trigger.evaluate("I read a book about suicide.", state, mock_llm)
    assert event is None


def test_13_multilingual(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "immediate_danger"
    }
    event = safety_trigger.evaluate("Mujhe bachao, wo mujhe maar dega", state, mock_llm)
    assert event is not None


def test_14_empty_invalid_message(safety_trigger, mock_llm):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    event = safety_trigger.evaluate("   ", state, mock_llm)
    assert event is None


def test_15_llm_unavailable(safety_trigger):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    event = safety_trigger.evaluate("Help", state, llm_provider=None)
    assert event is None


def test_16_alert_engine_unavailable():
    # If alert engine fails, it should catch the exception and return the event without crashing
    state = MedhaState(victim_id="V_1", session_id="S_1")
    
    class FailingAlertEngine:
        def emit_safety_event(self, event):
            raise ConnectionError("Network down")
            
    failing_trigger = SafetyTrigger(alert_engine=FailingAlertEngine())
    
    mock_llm = MockClassifyingLLMProvider()
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "immediate_danger"
    }
    
    # This should not raise an exception
    event = failing_trigger.evaluate("Help me", state, mock_llm)
    assert event is not None


def test_idempotency(safety_trigger, mock_llm, alert_engine):
    state = MedhaState(victim_id="V_1", session_id="S_1")
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "suicidal_intent"
    }
    
    # First time triggers
    event1 = safety_trigger.evaluate("I'm going to jump.", state, mock_llm)
    assert event1 is not None
    assert len(alert_engine.emitted_events) == 1
    
    # Second time with same trigger_type should be deduplicated
    event2 = safety_trigger.evaluate("I'm still going to jump.", state, mock_llm)
    assert event2 is None
    assert len(alert_engine.emitted_events) == 1


def test_pipeline_continuity_in_conversation_manager(test_manager, mock_llm):
    test_manager.create_session("VIC_1", "S_1")
    
    # 1. Normal message
    mock_llm.classification_result = {"safety_trigger": False}
    result1 = test_manager.process_message("S_1", "I'm stressed out.")
    assert result1.text_result is not None
    assert result1.text_result.text_available == 1.0
    
    # 2. Emergency message
    mock_llm.classification_result = {
        "safety_trigger": True,
        "trigger_type": "immediate_danger"
    }
    result2 = test_manager.process_message("S_1", "Someone is breaking in!")
    
    # The alert engine should have received the event
    assert len(test_manager.safety_trigger.alert_engine.emitted_events) == 1
    
    # Crucially, the MEDHA pipeline should NOT be blocked by the trigger.
    # We should still have text_result populated.
    assert result2.text_result is not None
    assert result2.text_result.text_available == 1.0
    assert "Text_Distress" in result2.state.text_features
