"""
Unit and Integration Tests for MEDHA Safety Gateway (Step 8)
============================================================

Verifies:
1. Clear conversation
2. Explicit supported safety observation (e.g., safety="unsafe")
3. Missing safety information is NOT false/zero
4. Negative language without evidence is ignored
5. High ML Risk does NOT trigger conversational safety
6. Structured conflict resolution (authoritative features win)
7. Evidence preservation
"""

import pytest
from chatbot.safety.safety_gateway import DeterministicSafetyGateway
from chatbot.state.medha_state import MedhaState

@pytest.fixture
def gateway():
    return DeterministicSafetyGateway()


def test_clear_conversation(gateway):
    """Test 1: Input contains no supported safety signal -> CLEAR."""
    state = MedhaState(victim_id="V1", timepoint=1)
    # Neutral candidate observations
    state.add_candidate_observation("mood", "neutral")
    state.add_candidate_observation("sleep", "fair")
    
    result = gateway.evaluate("I'm doing okay today.", state)
    
    assert not result.is_triggered
    assert result.category is None


def test_explicit_supported_safety_observation(gateway):
    """Test 2: Supported safety observation -> ESCALATE."""
    state = MedhaState(victim_id="V1", timepoint=1)
    state.add_candidate_observation(
        domain="safety", 
        semantic_value="in_danger",
        evidence="I don't feel safe here."
    )
    
    result = gateway.evaluate("I don't feel safe here.", state)
    
    assert result.is_triggered
    assert result.category == "conversational_safety"
    assert "source" in result.metadata
    assert result.metadata["source"] == "candidate_observation"
    assert "in_danger" in result.metadata["evidence"]


def test_missing_safety_information(gateway):
    """Test 3: Missing safety information does not mean safe, just no trigger."""
    state = MedhaState(victim_id="V1", timepoint=1)
    # State has no candidate observations and no structured features
    result = gateway.evaluate("I am feeling fine.", state)
    
    # Missing information just results in not triggered. 
    # It doesn't fabricate a "safe" observation in state.
    assert not result.is_triggered


def test_negative_language_without_safety_evidence(gateway):
    """Test 4: Negative language without safety evidence does not trigger."""
    state = MedhaState(victim_id="V1", timepoint=1)
    state.add_candidate_observation("mood", "very_low")
    state.add_candidate_observation("stress", "severe")
    
    result = gateway.evaluate("I'm having a terrible day. Everything is falling apart.", state)
    
    # Severe stress or very low mood is not an automatic emergency
    assert not result.is_triggered


def test_high_medha_risk_no_safety_signal(gateway):
    """Test 5: Simulate high V2 risk result without explicit safety condition."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    # Let's say earlier in the pipeline we know the user has high ML risk
    # But this is not checked by the SafetyGateway
    state.metadata["mock_temporal_risk"] = 0.95
    state.metadata["mock_dds"] = 99.0
    
    result = gateway.evaluate("I'm feeling stressed.", state)
    
    # The gateway must ignore ML predictions
    assert not result.is_triggered


def test_structured_conversational_conflict(gateway):
    """
    Test 6: Structured authoritative value wins.
    If the user has Threat_Event=1.0 in authoritative data, it triggers immediately, 
    regardless of what they are saying right now.
    """
    state = MedhaState(victim_id="V1", timepoint=1)
    state.structured_features["Threat_Event"] = 1.0
    
    # Even if they say they are fine
    state.add_candidate_observation("safety", "safe")
    
    result = gateway.evaluate("I am fine.", state)
    
    assert result.is_triggered
    assert result.category == "structured_threat"
    assert result.metadata["source"] == "structured"
    assert "Threat_Event == 1.0" in result.metadata["evidence"]


def test_evidence_preservation(gateway):
    """Test 7: SafetyResult contains the original evidence/provenance."""
    state = MedhaState(victim_id="V1", timepoint=1)
    state.add_candidate_observation("urgency", "critical", evidence="I need help right now.")
    
    result = gateway.evaluate("I need help right now.", state)
    
    assert result.is_triggered
    assert result.category == "conversational_urgency"
    assert result.metadata["source"] == "candidate_observation"
    assert "I need help right now." in result.metadata["evidence"]
