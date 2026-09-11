"""

Unit and Integration Tests for MedhaState
=========================================

Verifies:
- Empty state behavior (missing information remains missing)
- Partial state behavior (non-populated features remain None)
- Complete state behavior
- Missing optional modalities (strict preservation of missingness)
- NaN structured values (preservation of NaN, never coerced to 0)
- Conversation history tracking
- Question history and cooldown tracking
- Candidate observation separation
- Serialization and deserialization determinism
- Invalid feature names rejection (KeyError)
- Invalid data types rejection (TypeError)
"""

import json
import math
import pytest
import numpy as np

from chatbot.state.medha_state import (
    MedhaState,
    ChatMessage,
    QuestionRecord,
    CandidateObservation,
    ContextEvent,
    PreviousPrediction,
    STRUCTURED_FEATURES,
    STRUCTURED_CATEGORICAL_FEATURES,
    STRUCTURED_NUMERIC_FEATURES,
    TEXT_FEATURES,
    VOICE_FEATURES,
    BEHAVIOUR_FEATURES,
)


def test_empty_state():
    """Verify that an empty state initializes with exact schema and missing values."""
    state = MedhaState(victim_id="VIC_001", timepoint=1)

    assert state.victim_id == "VIC_001"
    assert state.timepoint == 1
    assert state.session_id.startswith("sess_")
    assert len(state.conversation_history) == 0
    assert state.current_user_message is None
    assert state.latest_assistant_response is None
    assert len(state.question_history) == 0
    assert len(state.candidate_observations) == 0

    # Structured features: exactly 42 features, all None
    assert len(state.structured_features) == 42
    assert all(val is None for val in state.structured_features.values())
    assert set(state.structured_features.keys()) == set(STRUCTURED_FEATURES)

    # Text features: exactly 5 features, all None
    assert len(state.text_features) == 5
    assert all(val is None for val in state.text_features.values())
    assert set(state.text_features.keys()) == set(TEXT_FEATURES)

    # Voice features: exactly 5 features, all None
    assert len(state.voice_features) == 5
    assert all(val is None for val in state.voice_features.values())
    assert set(state.voice_features.keys()) == set(VOICE_FEATURES)

    # Behaviour features: exactly 10 features, all None
    assert len(state.behaviour_features) == 10
    assert all(val is None for val in state.behaviour_features.values())
    assert set(state.behaviour_features.keys()) == set(BEHAVIOUR_FEATURES)

    # Availability: optional modalities start unassessed (None)
    assert state.text_available is None
    assert state.voice_available is None
    assert state.struct_available == 1.0
    assert state.behav_available == 1.0

    # Validation passes on clean empty state
    errors = state.validate()
    assert len(errors) == 0, f"Validation errors on empty state: {errors}"


def test_partial_state():
    """Verify that updating a subset of features leaves all other features missing."""
    state = MedhaState(victim_id="VIC_002", timepoint=2)

    # Update 2 structured features
    state.update_feature("structured", "Mood", 3.5)
    state.update_feature("structured", "Sleep", 2.0)

    # Check populated features
    populated = state.get_populated_structured_features()
    assert populated == {"Mood": 3.5, "Sleep": 2.0}

    # Remaining 40 features must still be None
    missing = state.get_missing_structured_features()
    assert len(missing) == 40
    assert "Mood" not in missing
    assert "Sleep" not in missing
    assert "Stress" in missing
    assert state.structured_features["Stress"] is None

    # Text, Voice, Behaviour still completely None
    assert all(v is None for v in state.text_features.values())
    assert all(v is None for v in state.voice_features.values())
    assert all(v is None for v in state.behaviour_features.values())


def test_complete_state():
    """Verify that a fully populated state satisfies schema and validation."""
    state = MedhaState(victim_id="VIC_COMPLETE", timepoint=3)

    # Populate all structured features
    for feat in STRUCTURED_NUMERIC_FEATURES:
        state.update_feature("structured", feat, 0.5)
    state.update_feature("structured", "Case_Type", "Domestic")
    state.update_feature("structured", "Case_Stage", "Investigation")
    state.update_feature("structured", "Episode_Severity", "Moderate")

    # Populate all text features
    for feat in TEXT_FEATURES:
        state.update_feature("text", feat, 0.42)
    state.set_modality_availability("text", 1.0)

    # Populate all voice features
    for feat in VOICE_FEATURES:
        state.update_feature("voice", feat, 0.88)
    state.set_modality_availability("voice", 1.0)

    # Populate all behaviour features
    for feat in BEHAVIOUR_FEATURES:
        state.update_feature("behaviour", feat, 0.15)

    assert len(state.get_missing_structured_features()) == 0
    assert len(state.get_populated_structured_features()) == 42
    assert state.is_modality_available("text") is True
    assert state.is_modality_available("voice") is True

    errors = state.validate()
    assert len(errors) == 0, f"Complete state validation failed: {errors}"


def test_missing_optional_modalities():
    """
    CRITICAL TEST: Missing optional modalities must NOT be converted to 0.0.
    When audio is absent, voice features must remain None/missing, Voice_Available = 0.0.
    """
    state = MedhaState(victim_id="VIC_NO_VOICE", timepoint=1)

    # User gave text only
    state.update_features_batch("text", {
        "Text_Distress": 0.75,
        "Fear": 0.60,
        "Threat_Context": 0.30,
        "Negative_Affect": 0.80,
        "Urgency": 0.50,
    })
    state.set_modality_availability("text", 1.0)

    # Voice was NOT provided
    state.set_modality_availability("voice", 0.0)

    assert state.text_available == 1.0
    assert state.voice_available == 0.0
    assert state.is_modality_available("text") is True
    assert state.is_modality_available("voice") is False

    # Voice features MUST remain None, NOT 0.0!
    for vf in VOICE_FEATURES:
        assert state.voice_features[vf] is None, f"Voice feature {vf} was improperly set!"

    # Serialization must preserve missing voice features as None
    state_dict = state.to_dict()
    assert state_dict["voice_available"] == 0.0
    for vf in VOICE_FEATURES:
        assert state_dict["voice_features"][vf] is None


def test_nan_structured_values():
    """Verify that NaN values are handled cleanly and preserved without converting to 0.0."""
    state = MedhaState(victim_id="VIC_NAN", timepoint=1)

    # Set NaN on numeric and categorical features
    state.update_feature("structured", "Mood", float("nan"))
    state.update_feature("structured", "Case_Type", float("nan"))

    assert math.isnan(state.structured_features["Mood"])
    assert math.isnan(state.structured_features["Case_Type"])

    # NaN counts as missing for V2 preprocessor readiness
    missing = state.get_missing_structured_features()
    assert "Mood" in missing
    assert "Case_Type" in missing

    # Serialization should clean NaN to None for JSON safety
    state_dict = state.to_dict()
    assert state_dict["structured_features"]["Mood"] is None
    assert state_dict["structured_features"]["Case_Type"] is None

    # to_json should succeed without JSON encoding errors
    json_str = state.to_json()
    assert json_str is not None


def test_conversation_history():
    """Verify multi-turn message appending and state tracking."""
    state = MedhaState(victim_id="VIC_CHAT", timepoint=1)

    m1 = state.add_user_message("Hello, I am feeling anxious today.")
    assert state.current_user_message == "Hello, I am feeling anxious today."
    assert len(state.conversation_history) == 1
    assert m1.role == "user"

    m2 = state.add_assistant_response("I hear you. Would you like to tell me what's making you anxious?")
    assert state.latest_assistant_response == "I hear you. Would you like to tell me what's making you anxious?"
    assert len(state.conversation_history) == 2
    assert m2.role == "assistant"

    m3 = state.add_system_message("Session checkin initialized.")
    assert len(state.conversation_history) == 3
    assert m3.role == "system"

    # History slice limit
    recent = state.get_history(limit=2)
    assert len(recent) == 2
    assert recent[0].role == "assistant"
    assert recent[1].role == "system"


def test_question_history():
    """Verify question tracking, answering, and cooldown evaluation."""
    state = MedhaState(victim_id="VIC_QE", timepoint=1)

    # Ask question GW-01 with a future cooldown
    q1 = state.record_question_asked(
        question_id="GW-01",
        question_text="Overall, how have you been feeling over the past few days?",
        intent="general_wellbeing",
        cooldown_until="2099-01-01T00:00:00+00:00",
    )
    assert state.get_last_question() == q1
    assert q1.answered is False
    assert len(state.get_unanswered_questions()) == 1

    # Cooldown should be active
    assert state.is_question_in_cooldown("GW-01", current_time_iso="2026-09-09T00:00:00+00:00") is True
    assert state.is_question_in_cooldown("GW-01", current_time_iso="2100-01-01T00:00:00+00:00") is False

    # Mark question answered
    success = state.record_question_answered("GW-01", "I've been feeling overwhelmed.")
    assert success is True
    assert q1.answered is True
    assert q1.response_text == "I've been feeling overwhelmed."
    assert len(state.get_unanswered_questions()) == 0


def test_candidate_observations_separation():
    """
    CRITICAL RULE: Candidate observations (e.g. sleep = poor) must remain
    qualitative records in candidate_observations and NOT alter numeric V2 features.
    """
    state = MedhaState(victim_id="VIC_OBS", timepoint=1)

    obs = state.add_candidate_observation(
        domain="sleep",
        semantic_value="poor",
        evidence="I haven't slept properly for three days.",
        status="candidate",
    )

    assert obs.domain == "sleep"
    assert obs.semantic_value == "poor"
    assert len(state.candidate_observations) == 1

    # The numeric Sleep feature in V2 MUST remain untouched (None)!
    assert state.structured_features["Sleep"] is None


def test_serialization_and_deserialization():
    """Verify complete round-trip JSON serialization and deserialization."""
    state = MedhaState(victim_id="VIC_SERIAL", session_id="sess_custom_123", timepoint=4)

    state.add_user_message("My hearing is tomorrow.")
    state.add_assistant_response("That can be very stressful.")
    state.record_question_asked("ES-02", "How are you coping with the upcoming hearing?", "event_stress")

    state.update_feature("structured", "Mood", 2.0)
    state.update_feature("structured", "Upcoming_Hearing", 1.0)
    state.update_feature("structured", "Case_Type", "Assault")
    state.update_feature("text", "Fear", 0.85)
    state.set_modality_availability("text", 1.0)
    state.set_modality_availability("voice", 0.0)

    state.add_event("hearing", "Court appearance scheduled for tomorrow morning.")
    state.record_prediction({
        "timepoint": 3,
        "fusion_dds": 52.4,
        "temporal_risk": 0.61,
        "temporal_available": 1,
        "future_escalation_flag": 0,
        "priority_level": "HIGH",
    })

    # Serialize to JSON
    json_str = state.to_json(indent=2)
    assert isinstance(json_str, str)

    # Deserialize back
    restored = MedhaState.from_json(json_str)

    assert restored.victim_id == "VIC_SERIAL"
    assert restored.session_id == "sess_custom_123"
    assert restored.timepoint == 4
    assert len(restored.conversation_history) == 2
    assert restored.conversation_history[0].content == "My hearing is tomorrow."
    assert len(restored.question_history) == 1
    assert restored.question_history[0].question_id == "ES-02"

    # Features
    assert restored.structured_features["Mood"] == 2.0
    assert restored.structured_features["Upcoming_Hearing"] == 1.0
    assert restored.structured_features["Case_Type"] == "Assault"
    assert restored.structured_features["Sleep"] is None  # still None!
    assert restored.text_features["Fear"] == 0.85
    assert restored.voice_features["Voice_Distress"] is None

    # Availability
    assert restored.text_available == 1.0
    assert restored.voice_available == 0.0
    assert restored.struct_available == 1.0

    # Events and predictions
    assert len(restored.recent_events) == 1
    assert restored.recent_events[0].event_type == "hearing"
    assert len(restored.previous_predictions) == 1
    assert restored.previous_predictions[0].fusion_dds == 52.4
    assert restored.previous_predictions[0].priority_level == "HIGH"


def test_invalid_feature_names():
    """Verify that unknown/hallucinated feature names are strictly rejected."""
    state = MedhaState(victim_id="VIC_ERR", timepoint=1)

    # Invalid structured feature
    with pytest.raises(KeyError, match="Unknown structured feature"):
        state.update_feature("structured", "Invented_Risk_Score", 10.0)

    # Invalid text feature
    with pytest.raises(KeyError, match="Unknown text feature"):
        state.update_feature("text", "Sentiment_Polarity", 0.5)

    # Invalid voice feature
    with pytest.raises(KeyError, match="Unknown voice feature"):
        state.update_feature("voice", "Pitch_Frequency", 120.0)

    # Invalid behaviour feature
    with pytest.raises(KeyError, match="Unknown behaviour feature"):
        state.update_feature("behaviour", "Typing_Speed", 50.0)

    # Invalid modality
    with pytest.raises(KeyError, match="Invalid modality"):
        state.update_feature("invalid_modality", "Mood", 1.0)


def test_invalid_data_types():
    """Verify that passing invalid data types raises TypeError."""
    state = MedhaState(victim_id="VIC_TYPE", timepoint=1)

    # Passing string to numeric feature
    with pytest.raises(TypeError, match="Numeric feature 'Mood' requires float, int, None, or NaN"):
        state.update_feature("structured", "Mood", "terrible")

    # Passing boolean to numeric feature
    with pytest.raises(TypeError, match="cannot be a boolean"):
        state.update_feature("structured", "Sleep", True)

    # Passing integer to categorical feature Case_Type
    with pytest.raises(TypeError, match="Categorical feature 'Case_Type' requires str, None, or NaN"):
        state.update_feature("structured", "Case_Type", 12345)


def test_invalid_state_creation():
    """Verify constructor validations for victim_id and timepoint."""
    with pytest.raises(ValueError, match="victim_id must be a non-empty string"):
        MedhaState(victim_id="")

    with pytest.raises(ValueError, match="victim_id must be a non-empty string"):
        MedhaState(victim_id="   ")

    with pytest.raises(ValueError, match="timepoint must be a positive integer >= 1"):
        MedhaState(victim_id="VIC_1", timepoint=0)

    with pytest.raises(ValueError, match="timepoint must be a positive integer >= 1"):
        MedhaState(victim_id="VIC_1", timepoint=-5)


def test_modality_availability_validation():
    """Verify validation on modality availability flags."""
    state = MedhaState(victim_id="VIC_AVAIL", timepoint=1)

    # Valid values
    state.set_modality_availability("text", 1.0)
    assert state.text_available == 1.0

    state.set_modality_availability("text", 0.0)
    assert state.text_available == 0.0

    state.set_modality_availability("text", True)
    assert state.text_available == 1.0

    state.set_modality_availability("text", None)
    assert state.text_available is None

    # Invalid flag value
    with pytest.raises(ValueError, match="Availability flag must be 1.0, 0.0, or None"):
        state.set_modality_availability("text", 2.5)

    with pytest.raises(TypeError, match="Invalid availability type"):
        state.set_modality_availability("text", "available")
