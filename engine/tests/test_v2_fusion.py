"""
MEDHA V2 Fusion Engine -- Unit Tests
======================================

Tests for the V2 Fusion Engine (Step 10B).
Covers schema, feature policy, missing modalities, bounds, serialization,
alignment, and forbidden feature detection.

Run with:
    python -m pytest engine/tests/test_v2_fusion.py -v
"""

import sys
import math
from pathlib import Path

import pytest
import numpy as np

# Ensure engine directory is in path
_current_dir = Path(__file__).resolve().parent
_engine_dir = _current_dir.parent
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir))

from v2.v2_fusion import (
    ModalitySignal,
    V2FusionInput,
    V2FusionOutput,
    compute_weighted_average_fusion,
    prepare_fusion_features,
    compute_learned_fusion,
    validate_fusion_features,
    V2_FUSION_APPROVED_FEATURES,
    V2_FUSION_AVAILABILITY_FLAGS,
    V2_FUSION_FORBIDDEN_FEATURES,
    _MODALITY_KEYS,
)


# ================================================================
# HELPERS
# ================================================================

DEFAULT_WEIGHTS = {
    "structured": 0.30,
    "text":       0.25,
    "voice":      0.25,
    "behaviour":  0.20,
}


def _make_input(
    victim_id="V0104",
    timepoint=28,
    structured=(True, 65.0),
    text=(True, 55.0),
    voice=(True, 60.0),
    behaviour=(True, 50.0),
) -> V2FusionInput:
    """Shorthand to build a V2FusionInput from (available, dds) tuples."""
    def _sig(pair):
        avail, dds = pair
        return ModalitySignal(available=avail, dds=dds if avail else None)

    return V2FusionInput(
        victim_id=victim_id,
        timepoint=timepoint,
        structured=_sig(structured),
        text=_sig(text),
        voice=_sig(voice),
        behaviour=_sig(behaviour),
    )


# ================================================================
# TEST 1: All four modalities available
# ================================================================

class TestAllAvailable:

    def test_fused_dds_formula(self):
        inp = _make_input()
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        expected = (
            0.30 * 65.0
            + 0.25 * 55.0
            + 0.25 * 60.0
            + 0.20 * 50.0
        )
        assert out.fusion_available is True
        assert out.fused_dds == pytest.approx(expected, abs=0.01)

    def test_effective_weights_equal_original(self):
        inp = _make_input()
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        for key in _MODALITY_KEYS:
            assert out.effective_weights[key] == pytest.approx(
                DEFAULT_WEIGHTS[key], abs=1e-6
            )


# ================================================================
# TESTS 2-5: Each modality individually missing
# ================================================================

@pytest.mark.parametrize("missing_key", [
    "voice",
    "text",
    "behaviour",
    "structured",
])
class TestOneMissing:

    def test_fusion_still_available(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.fusion_available is True

    def test_missing_weight_is_zero(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.effective_weights[missing_key] == 0.0

    def test_effective_weights_sum_to_one(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        total = sum(out.effective_weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_redistributed_weights_correct(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        available_keys = [k for k in _MODALITY_KEYS if k != missing_key]
        raw_sum = sum(DEFAULT_WEIGHTS[k] for k in available_keys)

        for key in available_keys:
            expected = DEFAULT_WEIGHTS[key] / raw_sum
            assert out.effective_weights[key] == pytest.approx(expected, abs=1e-6)


# ================================================================
# TEST 6: Text + Voice missing (common scenario, 24.7% of data)
# ================================================================

class TestTextVoiceMissing:

    def test_fusion_with_struct_behav_only(self):
        inp = _make_input(
            text=(False, None),
            voice=(False, None),
        )
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        assert out.fusion_available is True
        assert out.effective_weights["text"] == 0.0
        assert out.effective_weights["voice"] == 0.0

        # Weights should redistribute over structured + behaviour
        raw_sum = DEFAULT_WEIGHTS["structured"] + DEFAULT_WEIGHTS["behaviour"]
        assert out.effective_weights["structured"] == pytest.approx(
            DEFAULT_WEIGHTS["structured"] / raw_sum, abs=1e-6)
        assert out.effective_weights["behaviour"] == pytest.approx(
            DEFAULT_WEIGHTS["behaviour"] / raw_sum, abs=1e-6)

        expected = (
            (DEFAULT_WEIGHTS["structured"] / raw_sum) * 65.0
            + (DEFAULT_WEIGHTS["behaviour"] / raw_sum) * 50.0
        )
        assert out.fused_dds == pytest.approx(expected, abs=0.01)


# ================================================================
# TEST 7: Only one modality available
# ================================================================

@pytest.mark.parametrize("only_key,dds_val", [
    ("text", 40.0),
    ("voice", 30.0),
    ("behaviour", 80.0),
    ("structured", 60.0),
])
class TestOnlyOneAvailable:

    def test_fused_equals_that_modality(self, only_key, dds_val):
        kwargs = {
            "text": (False, None),
            "voice": (False, None),
            "behaviour": (False, None),
            "structured": (False, None),
        }
        kwargs[only_key] = (True, dds_val)
        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        assert out.fusion_available is True
        assert out.fused_dds == pytest.approx(dds_val, abs=0.01)
        assert out.effective_weights[only_key] == pytest.approx(1.0, abs=1e-6)


# ================================================================
# TEST 8: All modalities unavailable
# ================================================================

class TestAllUnavailable:

    def test_fusion_not_available(self):
        inp = _make_input(
            text=(False, None),
            voice=(False, None),
            behaviour=(False, None),
            structured=(False, None),
        )
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        assert out.fusion_available is False
        assert out.fused_dds is None

    def test_all_weights_zero(self):
        inp = _make_input(
            text=(False, None),
            voice=(False, None),
            behaviour=(False, None),
            structured=(False, None),
        )
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        for key in _MODALITY_KEYS:
            assert out.effective_weights[key] == 0.0


# ================================================================
# TEST 9: Fused DDS bounds (0-100)
# ================================================================

class TestFusedDDSBounds:

    def test_all_zero_dds(self):
        inp = _make_input(
            structured=(True, 0.0),
            text=(True, 0.0),
            voice=(True, 0.0),
            behaviour=(True, 0.0),
        )
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.fused_dds == pytest.approx(0.0, abs=0.01)

    def test_all_hundred_dds(self):
        inp = _make_input(
            structured=(True, 100.0),
            text=(True, 100.0),
            voice=(True, 100.0),
            behaviour=(True, 100.0),
        )
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.fused_dds == pytest.approx(100.0, abs=0.01)

    def test_mixed_dds_in_bounds(self):
        inp = _make_input()
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert 0.0 <= out.fused_dds <= 100.0


# ================================================================
# TEST 10: Metadata passthrough
# ================================================================

class TestMetadataPassthrough:

    def test_victim_id_unchanged(self):
        inp = _make_input(victim_id="V9999")
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.victim_id == "V9999"

    def test_timepoint_unchanged(self):
        inp = _make_input(timepoint=15)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        assert out.timepoint == 15


# ================================================================
# TEST 11: Serialization
# ================================================================

class TestSerialization:

    def test_to_dict_returns_plain_dict(self):
        inp = _make_input()
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        d = out.to_dict()

        assert isinstance(d, dict)
        assert d["victim_id"] == "V0104"
        assert d["fusion_available"] is True
        assert isinstance(d["specialist_predictions"], dict)
        assert isinstance(d["effective_weights"], dict)
        assert isinstance(d["fused_dds"], float)


# ================================================================
# TEST 12: Feature validation (forbidden features)
# ================================================================

class TestFeatureValidation:

    def test_approved_features_pass(self):
        validate_fusion_features(V2_FUSION_APPROVED_FEATURES + V2_FUSION_AVAILABILITY_FLAGS)

    def test_forbidden_feature_raises(self):
        with pytest.raises(ValueError, match="FORBIDDEN"):
            validate_fusion_features(["Struct_Pred", "Actual_DDS"])

    def test_dds_target_raises(self):
        with pytest.raises(ValueError, match="FORBIDDEN"):
            validate_fusion_features(["Struct_Pred", "DDS"])

    def test_future_escalation_raises(self):
        with pytest.raises(ValueError, match="FORBIDDEN"):
            validate_fusion_features(["Struct_Pred", "Future_Escalation_Label"])

    def test_previous_dds_raises(self):
        with pytest.raises(ValueError, match="FORBIDDEN"):
            validate_fusion_features(["Struct_Pred", "Previous_DDS"])

    def test_trajectory_state_raises(self):
        with pytest.raises(ValueError, match="FORBIDDEN"):
            validate_fusion_features(["Struct_Pred", "Trajectory_State"])

    def test_unknown_feature_raises(self):
        with pytest.raises(ValueError, match="UNKNOWN"):
            validate_fusion_features(["Struct_Pred", "Some_Random_Feature"])


# ================================================================
# TEST 13: prepare_fusion_features
# ================================================================

class TestPrepareFusionFeatures:

    def test_all_available(self):
        inp = _make_input(
            structured=(True, 65.0),
            text=(True, 55.0),
            voice=(True, 60.0),
            behaviour=(True, 50.0),
        )
        feats = prepare_fusion_features(inp)

        assert feats["Struct_Pred"] == 65.0
        assert feats["Text_Pred"] == 55.0
        assert feats["Voice_Pred"] == 60.0
        assert feats["Behav_Pred"] == 50.0
        assert feats["Struct_Available"] == 1.0
        assert feats["Text_Available"] == 1.0
        assert feats["Voice_Available"] == 1.0
        assert feats["Behav_Available"] == 1.0

    def test_missing_voice_imputed_zero(self):
        inp = _make_input(voice=(False, None))
        feats = prepare_fusion_features(inp)

        assert feats["Voice_Pred"] == 0.0
        assert feats["Voice_Available"] == 0.0

    def test_distinguishes_unavailable_from_zero(self):
        """Key test: prediction=0.0 with available=True vs unavailable."""
        inp_zero = _make_input(voice=(True, 0.0))
        inp_unavail = _make_input(voice=(False, None))

        feats_zero = prepare_fusion_features(inp_zero)
        feats_unavail = prepare_fusion_features(inp_unavail)

        # Both have Voice_Pred=0.0, but availability differs
        assert feats_zero["Voice_Pred"] == 0.0
        assert feats_zero["Voice_Available"] == 1.0  # available, prediction is 0

        assert feats_unavail["Voice_Pred"] == 0.0
        assert feats_unavail["Voice_Available"] == 0.0  # unavailable


# ================================================================
# TEST 14: Deterministic inference
# ================================================================

class TestDeterministicInference:

    def test_same_input_same_output(self):
        inp = _make_input()

        out1 = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)
        out2 = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        assert out1.fused_dds == out2.fused_dds
        assert out1.effective_weights == out2.effective_weights


# ================================================================
# TEST 15: Weights sum check
# ================================================================

class TestWeightsIntegrity:

    @pytest.mark.parametrize("n_missing", [0, 1, 2, 3])
    def test_weights_sum_to_one(self, n_missing):
        keys = list(DEFAULT_WEIGHTS.keys())
        kwargs = {}
        for i, key in enumerate(keys):
            if i < n_missing:
                kwargs[key] = (False, None)
            else:
                kwargs[key] = (True, 50.0)

        inp = _make_input(**kwargs)
        out = compute_weighted_average_fusion(inp, DEFAULT_WEIGHTS)

        if out.fusion_available:
            total = sum(out.effective_weights.values())
            assert total == pytest.approx(1.0, abs=1e-6)


# ================================================================
# TEST 16: No Actual_DDS leakage in feature preparation
# ================================================================

class TestNoLeakage:

    def test_actual_dds_not_in_features(self):
        """Verify Actual_DDS is never included in fusion features."""
        inp = _make_input()
        feats = prepare_fusion_features(inp)

        assert "Actual_DDS" not in feats
        assert "DDS" not in feats
        assert "Future_Escalation_Label" not in feats


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
