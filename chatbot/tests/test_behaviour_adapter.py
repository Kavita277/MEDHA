import math
import os
import sys
import pytest
from unittest.mock import MagicMock

# Add repository root to path so the script can be run directly via python
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from chatbot.engines.behaviour_adapter import MedhaBehaviourAdapter
from chatbot.state.medha_state import MedhaState
from chatbot.interfaces import PassThroughBehaviourAdapter

@pytest.fixture
def empty_state():
    return MedhaState(victim_id="TEST01", session_id="sess_123", timepoint=1)

@pytest.fixture
def behaviour_adapter():
    return MedhaBehaviourAdapter()

def test_1_valid_behaviour_input(empty_state, behaviour_adapter):
    """Test 1 - Valid behaviour input updates state correctly."""
    input_data = {
        "Engagement_Score": 85.5,
        "Missed_Checkin": 0,
        "Session_Duration_Minutes": 15
    }
    
    behaviour_adapter.process_and_update_state(empty_state, input_data)
    
    assert empty_state.behaviour_features["Engagement_Score"] == 85.5
    assert empty_state.behaviour_features["Missed_Checkin"] == 0.0
    assert empty_state.behaviour_features["Session_Duration_Minutes"] == 15.0
    assert empty_state.behav_available == 1.0


def test_2_canonical_feature_mapping(empty_state, behaviour_adapter):
    """Test 2 - Canonical feature mapping exactness."""
    # Input has extra junk features, should be ignored
    input_data = {
        "Engagement_Score": 85.5,
        "Random_Metric": 99.9,
        "Some_String": "Not allowed"
    }
    
    behaviour_adapter.process_and_update_state(empty_state, input_data)
    
    # Only Engagement_Score is kept
    assert empty_state.behaviour_features["Engagement_Score"] == 85.5
    assert "Random_Metric" not in empty_state.behaviour_features
    # Verify exact 10 keys exist in the dict
    assert len(empty_state.behaviour_features) == 10


def test_3_missing_behaviour(empty_state, behaviour_adapter):
    """Test 3 - Missing behaviour sets behav_available to 0.0."""
    behaviour_adapter.process_and_update_state(empty_state, None)
    
    assert empty_state.behav_available == 0.0
    for val in empty_state.behaviour_features.values():
        assert val is None


def test_4_invalid_input(empty_state, behaviour_adapter):
    """Test 4 - Invalid types are safely rejected."""
    input_data = {
        "Engagement_Score": "eighty five", # Invalid type
        "Missed_Checkin": None,
        "Session_Duration_Minutes": [1, 2, 3] # Invalid type
    }
    
    behaviour_adapter.process_and_update_state(empty_state, input_data)
    
    assert empty_state.behaviour_features["Engagement_Score"] is None
    assert empty_state.behaviour_features["Missed_Checkin"] is None
    assert empty_state.behaviour_features["Session_Duration_Minutes"] is None
    assert empty_state.behav_available == 0.0


def test_5_engine_failure_no_double_inference(empty_state):
    """
    Test 5 - Engine failure / double inference prevention.
    The adapter does not instantiate or run an ML model at all, guaranteeing no double inference.
    """
    adapter = MedhaBehaviourAdapter()
    assert not hasattr(adapter, "model")
    assert not hasattr(adapter, "preprocessor")


def test_6_no_conversational_fabrication(empty_state, behaviour_adapter):
    """
    Test 6 - Conversational semantic extraction does not map to numeric features.
    If LLM output gets misdirected to the adapter, it drops strings cleanly.
    """
    llm_output = {
        "Engagement_Score": "User seems disengaged.",
        "Behaviour_Trend": "getting worse"
    }
    
    behaviour_adapter.process_and_update_state(empty_state, llm_output)
    
    assert empty_state.behaviour_features["Engagement_Score"] is None
    assert empty_state.behaviour_features["Behaviour_Trend"] is None


def test_7_v2_integration_validation(empty_state, behaviour_adapter):
    """Test 7 & 8 - Verify it integrates smoothly into V2 DataFrame schema."""
    input_data = {
        "Engagement_Score": 70.0,
        "Engagement_Deviation": 2.5
    }
    behaviour_adapter.process_and_update_state(empty_state, input_data)
    
    # Simulate V2 Adapter conversion
    from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter
    v2_adapter = MedhaV2Adapter()
    
    df = v2_adapter.build_input_dataframe(empty_state)
    
    assert "Engagement_Score" in df.columns
    assert df["Engagement_Score"].iloc[0] == 70.0
    assert df["Engagement_Deviation"].iloc[0] == 2.5


def test_passthrough_adapter(empty_state):
    adapter = PassThroughBehaviourAdapter()
    adapter.process_and_update_state(empty_state, {"Engagement_Score": 99.0})
    
    assert empty_state.behav_available == 0.0
    assert empty_state.behaviour_features["Engagement_Score"] is None
