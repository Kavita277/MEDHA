"""
Unit and Integration Tests for MedhaTextAdapter
===============================================

Tests:
1. Normal chatbot message (full inference via existing MuRIL engine)
2. Short message handling
3. Empty and whitespace-only message handling (missingness preservation)
4. Multilingual message handling (Hindi & Hinglish supported by MuRIL)
5. Continuous probability preservation (no binarization or thresholding)
6. Source metadata pass-through (source="chatbot")
7. Text_Available behavior and state updates
8. Existing Text Engine failure handling
9. Mock engine dependency injection
10. Full integration: text adapter -> MedhaState -> MedhaV2Adapter -> predict_v2()
"""

import math
import pytest
from unittest.mock import MagicMock

from chatbot.engines.text_adapter import (
    MedhaTextAdapter,
    TextEngineResult,
    VECTOR_KEY_TO_V2_FEATURE,
)
from chatbot.state.medha_state import MedhaState, TEXT_FEATURES
from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline


@pytest.fixture(scope="module")
def shared_pipeline():
    """Module-scoped MedhaV2Pipeline instance."""
    return MedhaV2Pipeline()


@pytest.fixture(scope="module")
def real_text_adapter():
    """Module-scoped MedhaTextAdapter using the real MuRIL Text Engine."""
    return MedhaTextAdapter()


# ===========================================================================
# TEST 1 — Normal Chatbot Message
# ===========================================================================
def test_normal_chatbot_message(real_text_adapter):
    """Verify normal conversational message produces all 5 continuous text features."""
    text = "I am extremely scared about what might happen at the court hearing tomorrow."
    result = real_text_adapter.analyze_text(
        text=text,
        victim_id="VIC_TXT_01",
        session_id="SESS_TXT_01",
        source="chatbot",
    )

    assert isinstance(result, TextEngineResult)
    assert result.text_available == 1.0
    assert result.source == "chatbot"
    assert result.error_message is None

    # Exact 5 canonical V2 text features
    assert set(result.features.keys()) == set(TEXT_FEATURES)

    # All values must be valid continuous floats in [0.0, 1.0]
    for feat_name, prob in result.features.items():
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0
        assert not math.isnan(prob)

    # Fear should be distinctly elevated for this statement
    assert result.features["Fear"] > 0.5


# ===========================================================================
# TEST 2 — Short Message
# ===========================================================================
def test_short_message(real_text_adapter):
    """Verify that short messages run through MuRIL without truncation/shape errors."""
    result = real_text_adapter.analyze_text(text="I'm okay.", source="chatbot")

    assert result.text_available == 1.0
    assert len(result.features) == 5
    for feat in TEXT_FEATURES:
        assert isinstance(result.features[feat], float)
        assert 0.0 <= result.features[feat] <= 1.0


# ===========================================================================
# TEST 3 — Empty and Whitespace-only Message
# ===========================================================================
def test_empty_and_whitespace_message(real_text_adapter):
    """
    CRITICAL RULE: Empty/whitespace text must NOT be sent to MuRIL.
    Text_Available must be 0.0, and features must remain None (never 0.0).
    """
    for empty_input in [None, "", "   ", "\n\t  \r\n"]:
        result = real_text_adapter.analyze_text(text=empty_input, source="chatbot")

        assert result.text_available == 0.0
        assert result.raw_vector is None
        assert result.error_message is None

        # Features must be None (missingness preserved!)
        for feat in TEXT_FEATURES:
            assert result.features[feat] is None, f"Feature '{feat}' was not None for empty input!"

    # Test state update with empty text
    state = MedhaState(victim_id="VIC_EMPTY_TXT", timepoint=1)
    real_text_adapter.process_and_update_state(state, "   ")

    assert state.text_available == 0.0
    assert all(val is None for val in state.text_features.values())


# ===========================================================================
# TEST 4 — Multilingual Messages (Hindi & Hinglish)
# ===========================================================================
def test_multilingual_messages(real_text_adapter):
    """Verify that the MuRIL model processes Hindi and Hinglish inputs accurately."""
    # Hindi
    hi_text = "मुझे बहुत डर लग रहा है कि आगे क्या होगा और मैं अपने परिवार को लेकर बहुत चिंतित हूँ।"
    hi_result = real_text_adapter.analyze_text(text=hi_text, language="hi", source="chatbot")

    assert hi_result.text_available == 1.0
    assert hi_result.language == "hi"
    for feat in TEXT_FEATURES:
        assert isinstance(hi_result.features[feat], float)
        assert 0.0 <= hi_result.features[feat] <= 1.0

    # Hinglish
    hinglish_text = "Mujhe bahut darr lag raha hai aur tension ho rahi hai ki aage kya hoga."
    hinglish_result = real_text_adapter.analyze_text(text=hinglish_text, language="hinglish", source="chatbot")

    assert hinglish_result.text_available == 1.0
    assert hinglish_result.language == "hinglish"
    for feat in TEXT_FEATURES:
        assert isinstance(hinglish_result.features[feat], float)
        assert 0.0 <= hinglish_result.features[feat] <= 1.0


# ===========================================================================
# TEST 5 — Continuous Probability Preservation
# ===========================================================================
def test_continuous_probability_preservation(real_text_adapter):
    """
    CRITICAL RULE: Probabilities must NOT be binarized (into 0 or 1)
    or manually thresholded. Continuous floats with full decimal precision must be preserved.
    """
    result = real_text_adapter.analyze_text(
        text="I am feeling a little nervous about tomorrow, but mostly tired."
    )

    assert result.text_available == 1.0

    # At least one probability should be a non-trivial decimal between 0.01 and 0.99
    has_continuous_value = False
    for prob in result.features.values():
        if 0.001 < prob < 0.999:
            has_continuous_value = True
        # Verify it's not an integer 0 or 1
        assert prob not in (0, 1)

    assert has_continuous_value, "Outputs appear artificially discretized!"


# ===========================================================================
# TEST 6 — Source Metadata
# ===========================================================================
def test_source_metadata(real_text_adapter):
    """Verify source metadata is strictly passed as 'chatbot'."""
    result = real_text_adapter.analyze_text(
        text="Everything has been stressful lately.",
        source="chatbot",
    )

    assert result.source == "chatbot"


# ===========================================================================
# TEST 7 — Text_Available Behavior and State Updates
# ===========================================================================
def test_text_available_behavior(real_text_adapter):
    """Verify process_and_update_state updates MedhaState with exact features and flags."""
    state = MedhaState(victim_id="VIC_STATE_TXT", timepoint=1)

    # Initial state: unassessed
    assert state.text_available is None

    # Provide real text
    real_text_adapter.process_and_update_state(
        state=state,
        text="I have been crying all day and feel hopeless.",
        source="chatbot",
    )

    assert state.text_available == 1.0
    assert state.is_modality_available("text") is True

    for feat in TEXT_FEATURES:
        assert state.text_features[feat] is not None
        assert 0.0 <= state.text_features[feat] <= 1.0

    # All 5 canonical features populated as continuous floats
    for feat in TEXT_FEATURES:
        assert isinstance(state.text_features[feat], float)
        assert 0.0 <= state.text_features[feat] <= 1.0


# ===========================================================================
# TEST 8 — Existing Text Engine Failure Handling
# ===========================================================================
def test_existing_text_engine_failure():
    """Verify safe error handling when the underlying Text Engine raises an exception."""
    # Mock engine that raises an error
    failing_engine = MagicMock(side_effect=RuntimeError("CUDA out of memory or device error"))

    # With raise_on_error=False (default safe mode)
    adapter = MedhaTextAdapter(engine_fn=failing_engine, raise_on_error=False)
    result = adapter.analyze_text(text="Some text")

    assert result.text_available == 0.0
    assert result.error_message is not None
    assert "CUDA out of memory" in result.error_message
    assert all(v is None for v in result.features.values())

    # With raise_on_error=True
    strict_adapter = MedhaTextAdapter(engine_fn=failing_engine, raise_on_error=True)
    with pytest.raises(RuntimeError, match="CUDA out of memory"):
        strict_adapter.analyze_text(text="Some text")


# ===========================================================================
# TEST 9 — Mock Engine Injection
# ===========================================================================
def test_mock_engine_injection():
    """Verify dependency injection of custom engine function matching the contract."""
    mock_engine = MagicMock(return_value={
        "victim_id": "V_MOCK",
        "session_id": "S_MOCK",
        "source": "chatbot",
        "text_available": 1,
        "text_vector": {
            "text_distress": 0.4567,
            "fear_signal": 0.1234,
            "threat_context": 0.8901,
            "negative_affect": 0.6543,
            "urgency": 0.2345,
        },
    })

    adapter = MedhaTextAdapter(engine_fn=mock_engine)
    result = adapter.analyze_text(text="Testing injection", victim_id="V_MOCK", session_id="S_MOCK")

    mock_engine.assert_called_once()
    assert result.text_available == 1.0
    assert result.features["Text_Distress"] == 0.4567
    assert result.features["Fear"] == 0.1234
    assert result.features["Threat_Context"] == 0.8901
    assert result.features["Negative_Affect"] == 0.6543
    assert result.features["Urgency"] == 0.2345


# ===========================================================================
# TEST 10 — Full Integration: Text Adapter -> MedhaState -> MedhaV2Adapter -> predict_v2()
# ===========================================================================
def test_full_pipeline_text_integration(real_text_adapter, shared_pipeline):
    """
    Verifies the complete vertical chain:
    User message -> Text Engine -> 5 features -> MedhaState -> V2 Adapter -> predict_v2().
    """
    # 1. User says something in chat
    user_message = "I am terrified they will hurt me again after the trial."

    # 2. Initialize MedhaState
    state = MedhaState(victim_id="VIC_CHAIN_01", timepoint=1)
    state.add_user_message(user_message)

    # 3. Analyze text and update state
    text_result = real_text_adapter.process_and_update_state(state, user_message)
    assert text_result.text_available == 1.0

    # 4. Pass to MedhaV2Adapter
    v2_adapter = MedhaV2Adapter(pipeline=shared_pipeline, enable_triage=True)
    v2_result = v2_adapter.predict(state)

    # 5. Verify V2 pipeline consumed the Text Specialist outputs
    assert v2_result.text_available == 1.0
    assert v2_result.text_pred is not None
    assert 0.0 <= v2_result.text_pred <= 100.0

    # 6. Current DDS computed
    assert 0.0 <= v2_result.current_dds <= 100.0
    assert v2_result.priority_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
