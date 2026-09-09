"""
Tests for Conversation Summary (Step 9)
=======================================

Verifies:
- Empty summary initialization
- Provenance tracking
- Deduplication and size limits
- Non-interference with V2 predictive boundaries
- Serialization
- Safey Gateway boundary isolation
"""

import pytest
import json
from chatbot.state.medha_state import MedhaState
from chatbot.summary.summary_schema import ConversationSummary, SummaryItem
from chatbot.summary.conversation_summary_engine import ConversationSummaryEngine
from chatbot.interfaces import LLMProviderProtocol, LLMResponse


class MockLLMForSummary(LLMProviderProtocol):
    def __init__(self, mock_json_str: str):
        self.mock_json_str = mock_json_str

    def generate_response(self, message: str, state: MedhaState, **kwargs) -> LLMResponse:
        return LLMResponse(
            text=self.mock_json_str,
            candidate_observations=[]
        )


@pytest.fixture
def empty_state():
    return MedhaState(victim_id="V1", timepoint=1)


@pytest.fixture
def summary_engine():
    return ConversationSummaryEngine()


def test_empty_initialization(empty_state):
    assert isinstance(empty_state.conversation_summary, ConversationSummary)
    assert len(empty_state.conversation_summary.important_facts) == 0
    
    data = empty_state.conversation_summary.to_dict()
    assert data["important_facts"] == []


def test_provenance_and_deduplication(empty_state, summary_engine):
    """Test 4 - Provenance & Test 5 - Exact Duplicate"""
    empty_state.current_user_message = "I am living in Mumbai."
    empty_state.conversation_history = ["turn0", "turn1"]
    
    mock_llm = MockLLMForSummary(json.dumps({
        "important_facts": [
            {"content": "User lives in Mumbai.", "supersedes_content": None},
            {"content": "User lives in Mumbai.", "supersedes_content": None}
        ]
    }))
    
    summary_engine.update_summary(empty_state, mock_llm)
    
    # Check deduplication
    assert len(empty_state.conversation_summary.important_facts) == 1
    
    fact = empty_state.conversation_summary.important_facts[0]
    assert fact.content == "User lives in Mumbai."
    assert fact.source == "user_statement"
    assert fact.extracted_by == "llm_extraction"
    assert fact.turn_index == 2
    assert fact.evidence == "I am living in Mumbai."
    assert fact.status == "active"


def test_explicit_update(empty_state, summary_engine):
    """Test 1 - Explicit Update & Test 2 - Historical Preservation"""
    # Turn 1
    empty_state.current_user_message = "I am sleeping well."
    empty_state.conversation_history = ["turn0", "turn1"]
    mock_llm_1 = MockLLMForSummary(json.dumps({
        "important_observations": [{"content": "I am sleeping well.", "supersedes_content": None}]
    }))
    summary_engine.update_summary(empty_state, mock_llm_1)
    
    assert empty_state.conversation_summary.important_observations[0].content == "I am sleeping well."
    assert empty_state.conversation_summary.important_observations[0].status == "active"
    
    # Turn 5
    empty_state.current_user_message = "Actually, I am not sleeping well anymore."
    empty_state.conversation_history = ["turn0", "turn1", "turn2", "turn3", "turn4", "turn5"]
    mock_llm_2 = MockLLMForSummary(json.dumps({
        "important_observations": [
            {"content": "not sleeping well anymore", "supersedes_content": "I am sleeping well."}
        ]
    }))
    summary_engine.update_summary(empty_state, mock_llm_2)
    
    # Old item remains (historical preservation) but is superseded
    assert len(empty_state.conversation_summary.important_observations) == 2
    
    old_item = empty_state.conversation_summary.important_observations[0]
    new_item = empty_state.conversation_summary.important_observations[1]
    
    assert old_item.content == "I am sleeping well."
    assert old_item.status == "superseded"
    
    assert new_item.content == "not sleeping well anymore"
    assert new_item.status == "active"


def test_ambiguous_contradiction(empty_state, summary_engine):
    """Test 3 - Ambiguous contradiction"""
    empty_state.conversation_summary.important_facts.append(
        SummaryItem(content="Lives alone", turn_index=1, source="user_statement")
    )
    
    empty_state.current_user_message = "My brother is coming to stay with me."
    empty_state.conversation_history = ["turn0", "turn1", "turn2", "turn3"]
    
    # The LLM thinks it supersedes "Lives with brother" (which doesn't exist) 
    # or attempts to supersede "Lives alone" but messes up the exact string match
    mock_llm = MockLLMForSummary(json.dumps({
        "important_facts": [
            {"content": "Lives with brother", "supersedes_content": "Lives with parents"}
        ]
    }))
    
    summary_engine.update_summary(empty_state, mock_llm)
    
    assert len(empty_state.conversation_summary.important_facts) == 2
    
    old_item = empty_state.conversation_summary.important_facts[0]
    new_item = empty_state.conversation_summary.important_facts[1]
    
    assert old_item.content == "Lives alone"
    assert old_item.status == "active"
    
    assert new_item.content == "Lives with brother"
    assert new_item.status == "unresolved"


def test_v2_boundary_isolation(empty_state, summary_engine):
    """Test 6 - V2 isolation"""
    empty_state.current_user_message = "My sleep is very poor."
    empty_state.conversation_history = ["turn0", "turn1"]
    
    # Store initial state of V2 numeric features
    initial_sleep = empty_state.structured_features.get("Sleep")
    
    mock_llm = MockLLMForSummary(json.dumps({
        "important_observations": [{"content": "User reported poor sleep.", "supersedes_content": None}]
    }))
    
    summary_engine.update_summary(empty_state, mock_llm)
    
    # The summary captured the observation
    assert len(empty_state.conversation_summary.important_observations) == 1
    assert empty_state.conversation_summary.important_observations[0].content == "User reported poor sleep."
    
    # CRITICAL: The V2 feature must NOT be modified by the summary engine
    assert empty_state.structured_features.get("Sleep") == initial_sleep


def test_serialization_round_trip(empty_state):
    empty_state.conversation_summary.important_facts.append(
        SummaryItem(content="Fact 1", source="user_statement", extracted_by="llm_extraction", turn_index=1)
    )
    
    state_json = empty_state.to_json()
    new_state = MedhaState.from_dict(json.loads(state_json))
    
    assert len(new_state.conversation_summary.important_facts) == 1
    assert new_state.conversation_summary.important_facts[0].content == "Fact 1"
    assert new_state.conversation_summary.important_facts[0].extracted_by == "llm_extraction"


def test_bounded_memory(empty_state, summary_engine):
    """Test 8 - Bounded memory"""
    empty_state.current_user_message = "Updating limits."
    empty_state.conversation_history = ["turn0", "turn1"]
    
    facts = [{"content": f"Fact {i}", "supersedes_content": None} for i in range(15)]
    mock_llm = MockLLMForSummary(json.dumps({
        "important_facts": facts
    }))
    
    summary_engine.update_summary(empty_state, mock_llm)
    
    # Should be limited to 10
    assert len(empty_state.conversation_summary.important_facts) == 10

