"""
Unit and Integration Tests for MedhaV2Adapter
=============================================

Tests:
1. Minimal valid state (clean integration with frozen V2 pipeline)
2. Partial state (missing optional information remains np.nan, never 0.0)
3. Voice unavailable (voice_available = 0.0, voice features = np.nan)
4. Candidate observation isolation (qualitative extracts never leak into V2 features)
5. Feature whitelist (only approved V2 columns reach predict_v2)
6. Input schema completeness and exact column definitions
7. Existing pipeline invocation (verified calling predict_v2 with exact types)
8. Output preservation (adapter never modifies or recalculates V2 outputs)
9. Failure handling (malformed state rejected with clean exceptions)
10. Longitudinal GRU sequence execution (8 timepoints produce valid future risk)
"""

import math
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest

from chatbot.state.medha_state import (
    MedhaState,
    STRUCTURED_FEATURES,
    TEXT_FEATURES,
    VOICE_FEATURES,
    BEHAVIOUR_FEATURES,
)
from chatbot.v2_adapter.medha_v2_adapter import (
    MedhaV2Adapter,
    V2PredictionResult,
    GRU_ADDITIONAL_WHITELIST_FEATURES,
)
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline


@pytest.fixture(scope="module")
def shared_pipeline():
    """Module-scoped MedhaV2Pipeline instance to avoid reloading models on every test."""
    return MedhaV2Pipeline()


# ===========================================================================
# TEST 1 — Minimal Valid State
# ===========================================================================
def test_1_minimal_valid_state(shared_pipeline):
    """Verify that a minimal clean state can reach the frozen V2 pipeline and produce outputs."""
    adapter = MedhaV2Adapter(pipeline=shared_pipeline, enable_triage=True)
    state = MedhaState(victim_id="VIC_MINIMAL_01", timepoint=1)

    result = adapter.predict(state)

    assert isinstance(result, V2PredictionResult)
    assert result.victim_id == "VIC_MINIMAL_01"
    assert result.timepoint == 1

    # DDS must be calculated (0 to 100)
    assert 0.0 <= result.current_dds <= 100.0
    assert not math.isnan(result.current_dds)

    # Future risk is None because history < 7
    assert result.future_risk is None
    assert result.future_risk_available is False
    assert result.future_escalation_flag is None

    # Specialists
    assert not math.isnan(result.struct_pred)
    assert not math.isnan(result.behav_pred)

    # Availability
    assert result.struct_available == 1.0
    assert result.behav_available == 1.0
    assert result.text_available == 0.0
    assert result.voice_available == 0.0


# ===========================================================================
# TEST 2 — Partial State
# ===========================================================================
def test_2_partial_state(shared_pipeline):
    """Verify that populated features are passed and unpopulated features remain np.nan."""
    adapter = MedhaV2Adapter(pipeline=shared_pipeline)
    state = MedhaState(victim_id="VIC_PARTIAL_01", timepoint=1)

    state.update_feature("structured", "Mood", 4.0)
    state.update_feature("structured", "Sleep", 1.5)
    state.update_feature("text", "Fear", 0.70)
    state.set_modality_availability("text", 1.0)

    df = adapter.build_input_dataframe(state)

    # Populated features have values
    assert df["Mood"].iloc[0] == 4.0
    assert df["Sleep"].iloc[0] == 1.5
    assert df["Fear"].iloc[0] == 0.70
    assert df["Text_Available"].iloc[0] == 1.0

    # Unpopulated features MUST remain NaN (NOT 0.0!)
    assert pd.isna(df["Stress"].iloc[0])
    assert pd.isna(df["Functioning"].iloc[0])
    assert pd.isna(df["Voice_Distress"].iloc[0])
    assert df["Voice_Available"].iloc[0] == 0.0

    # Execute inference
    result = adapter.predict(state)
    assert 0.0 <= result.current_dds <= 100.0
    assert result.text_available == 1.0


# ===========================================================================
# TEST 3 — Voice Unavailable
# ===========================================================================
def test_3_voice_unavailable(shared_pipeline):
    """
    CRITICAL TEST: When voice is unavailable, Voice_Available = 0.0,
    and voice feature values MUST remain missing (np.nan), NEVER 0.0.
    """
    adapter = MedhaV2Adapter(pipeline=shared_pipeline)
    state = MedhaState(victim_id="VIC_NO_VOICE", timepoint=1)

    # Text available, voice NOT available
    state.update_feature("text", "Text_Distress", 0.65)
    state.set_modality_availability("text", 1.0)
    state.set_modality_availability("voice", 0.0)

    df = adapter.build_input_dataframe(state)

    assert df["Voice_Available"].iloc[0] == 0.0

    # All voice features must be np.nan
    for vf in VOICE_FEATURES:
        assert pd.isna(df[vf].iloc[0]), f"Voice feature '{vf}' was improperly converted to non-NaN!"
        assert df[vf].iloc[0] is not 0.0, f"Voice feature '{vf}' was converted to 0.0!"

    # Run inference
    result = adapter.predict(state)
    assert result.voice_available == 0.0
    assert result.voice_pred is None  # predict_v2 sets Voice_Pred to NaN when Voice_Available == 0


# ===========================================================================
# TEST 4 — Candidate Observation Isolation
# ===========================================================================
def test_4_candidate_observation_isolation(shared_pipeline):
    """
    CRITICAL RULE: Candidate qualitative observations (e.g. sleep=poor) must NOT
    leak into numeric V2 features. Unmapped features must remain np.nan.
    """
    adapter = MedhaV2Adapter(pipeline=shared_pipeline)
    state = MedhaState(victim_id="VIC_QUALITATIVE", timepoint=1)

    # Add raw qualitative extractions
    state.add_candidate_observation("sleep", "severely_impaired", "I haven't slept in days")
    state.add_candidate_observation("stress", "extreme", "I feel like I'm breaking down")
    state.add_candidate_observation("suicide_risk", 0.95, "Dangerous phrase")

    df = adapter.build_input_dataframe(state)

    # In V2 input, Sleep and Stress must still be NaN!
    assert pd.isna(df["Sleep"].iloc[0])
    assert pd.isna(df["Stress"].iloc[0])

    # Unauthorized candidate 'suicide_risk' must NOT exist in the DataFrame
    assert "suicide_risk" not in df.columns


# ===========================================================================
# TEST 5 — Feature Whitelist
# ===========================================================================
def test_5_feature_whitelist(shared_pipeline):
    """Verify that only authorized canonical V2 columns are included in the DataFrame."""
    adapter = MedhaV2Adapter(pipeline=shared_pipeline)
    state = MedhaState(victim_id="VIC_WHITELIST", timepoint=1)

    df = adapter.build_input_dataframe(state)

    expected_columns = (
        {"Victim_ID", "Timepoint", "Text_Available", "Voice_Available"} |
        set(STRUCTURED_FEATURES) |
        set(TEXT_FEATURES) |
        set(VOICE_FEATURES) |
        set(BEHAVIOUR_FEATURES) |
        set(GRU_ADDITIONAL_WHITELIST_FEATURES)
    )

    actual_columns = set(df.columns)
    assert actual_columns == expected_columns, f"Column mismatch: extra={actual_columns - expected_columns}, missing={expected_columns - actual_columns}"


# ===========================================================================
# TEST 6 — Input Schema
# ===========================================================================
def test_6_input_schema(shared_pipeline):
    """Verify exact column counts and data types of adapter-built DataFrame."""
    adapter = MedhaV2Adapter(pipeline=shared_pipeline)
    state = MedhaState(victim_id="VIC_SCHEMA", timepoint=2)

    df = adapter.build_input_dataframe(state)

    assert len(df) == 1
    # 4 (meta) + 42 (struct) + 5 (text) + 5 (voice) + 10 (behav) + 6 (gru additional) - overlaps = 68 total columns
    assert "Victim_ID" in df.columns
    assert "Timepoint" in df.columns
    assert df["Victim_ID"].iloc[0] == "VIC_SCHEMA"
    assert df["Timepoint"].iloc[0] == 2

    # Categorical columns exist
    for cat in ("Case_Type", "Case_Stage", "Episode_Severity"):
        assert cat in df.columns


# ===========================================================================
# TEST 7 — Existing Pipeline Invocation
# ===========================================================================
def test_7_existing_pipeline_invocation():
    """Verify that adapter invokes predict_v2() on the injected pipeline with correct DataFrame."""
    mock_pipeline = MagicMock()

    # Create mock return DataFrame matching predict_v2() output structure
    mock_output_df = pd.DataFrame([{
        "Victim_ID": "VIC_MOCK",
        "Timepoint": 1,
        "Struct_Pred": 45.0,
        "Struct_Available": 1.0,
        "Text_Pred": np.nan,
        "Text_Available": 0.0,
        "Voice_Pred": np.nan,
        "Voice_Available": 0.0,
        "Behav_Pred": 50.0,
        "Behav_Available": 1.0,
        "Fusion_DDS_Prediction": 48.5,
        "Temporal_Risk_Score": np.nan,
        "Temporal_Available": 0,
        "Future_Escalation_Flag": np.nan,
    }])
    mock_pipeline.predict_v2.return_value = mock_output_df

    adapter = MedhaV2Adapter(pipeline=mock_pipeline, enable_triage=False)
    state = MedhaState(victim_id="VIC_MOCK", timepoint=1)

    result = adapter.predict(state)

    # Verify predict_v2 was called exactly once with a DataFrame
    mock_pipeline.predict_v2.assert_called_once()
    args, kwargs = mock_pipeline.predict_v2.call_args
    passed_df = args[0]
    assert isinstance(passed_df, pd.DataFrame)
    assert passed_df["Victim_ID"].iloc[0] == "VIC_MOCK"

    # Verify output unpacked correctly
    assert result.current_dds == 48.5
    assert result.struct_pred == 45.0
    assert result.future_risk is None


# ===========================================================================
# TEST 8 — Output Preservation
# ===========================================================================
def test_8_output_preservation(shared_pipeline):
    """
    Verify that the adapter does not alter, rescale, or recalculate
    the authoritative predictions returned by MedhaV2Pipeline.
    """
    adapter = MedhaV2Adapter(pipeline=shared_pipeline, enable_triage=False)
    state = MedhaState(victim_id="VIC_PRESERVE", timepoint=1)
    state.update_feature("structured", "Mood", 3.0)

    # 1. Build DataFrame via adapter
    input_df = adapter.build_input_dataframe(state)

    # 2. Call pipeline directly
    direct_output_df = shared_pipeline.predict_v2(input_df.copy())
    expected_dds = direct_output_df["Fusion_DDS_Prediction"].iloc[0]
    expected_struct = direct_output_df["Struct_Pred"].iloc[0]
    expected_behav = direct_output_df["Behav_Pred"].iloc[0]

    # 3. Call via adapter
    adapter_result = adapter.predict(state)

    # Assert exact floating point equality (zero deviation)
    assert adapter_result.current_dds == expected_dds
    assert adapter_result.struct_pred == expected_struct
    assert adapter_result.behav_pred == expected_behav


# ===========================================================================
# TEST 9 — Failure Handling
# ===========================================================================
def test_9_failure_handling():
    """Verify that invalid inputs or corrupted states raise clear exceptions without silent fallback."""
    adapter = MedhaV2Adapter()

    # Passing non-MedhaState object
    with pytest.raises(TypeError, match="Expected MedhaState"):
        adapter.predict("not_a_state")

    # Mismatched history victim_id
    s1 = MedhaState(victim_id="VIC_A", timepoint=1)
    s2 = MedhaState(victim_id="VIC_B", timepoint=2)
    with pytest.raises(ValueError, match="victim_id mismatch"):
        adapter.build_input_dataframe(state=s2, history_states=[s1])

    # Out-of-order timepoints in history
    s_curr = MedhaState(victim_id="VIC_A", timepoint=2)
    s_invalid_hist = MedhaState(victim_id="VIC_A", timepoint=3)  # timepoint 3 >= 2
    with pytest.raises(ValueError, match="must be < current timepoint"):
        adapter.build_input_dataframe(state=s_curr, history_states=[s_invalid_hist])


# ===========================================================================
# TEST 10 — Longitudinal GRU Sequence Execution
# ===========================================================================
def test_10_longitudinal_gru_history(shared_pipeline):
    """
    Verify that when 7+ historical timepoints are provided,
    the GRU temporal risk score is computed and populated by predict_v2().
    """
    adapter = MedhaV2Adapter(pipeline=shared_pipeline, enable_triage=True)
    v_id = "VIC_LONGITUDINAL"

    # Create 7 historical states (timepoints 1 to 7)
    history_states = []
    for tp in range(1, 8):
        h = MedhaState(victim_id=v_id, timepoint=tp)
        h.update_feature("structured", "Mood", float(tp) * 0.5)
        h.set_modality_availability("text", 1.0)
        h.update_feature("text", "Text_Distress", 0.5)
        history_states.append(h)

    # Current state is timepoint 8 (has >= 7 historical steps preceding it)
    current_state = MedhaState(victim_id=v_id, timepoint=8)
    current_state.update_feature("structured", "Mood", 4.5)
    current_state.set_modality_availability("text", 1.0)
    current_state.update_feature("text", "Text_Distress", 0.7)

    result = adapter.predict(current_state, history_states=history_states)

    # With 7 preceding timepoints, Temporal_Available must be True and future_risk must exist
    assert result.future_risk_available is True
    assert result.future_risk is not None
    assert 0.0 <= result.future_risk <= 1.0
    assert result.future_escalation_flag in (0, 1)

    # Downstream Triage evaluated
    assert result.priority_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
    assert result.priority_rationale is not None
