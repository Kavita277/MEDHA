"""
MEDHA Fusion Engine — Unit Tests
===================================

Tests 1–16 as specified in the fusion requirements, plus additional
edge-case and adapter tests.

Run with:
    python -m pytest engine/fusion_engine/test_fusion.py -v
"""

import math
import sys
from pathlib import Path
import pytest

# Ensure parent directory is in sys.path when running script directly
_current_dir = Path(__file__).resolve().parent
if str(_current_dir.parent) not in sys.path:
    sys.path.insert(0, str(_current_dir.parent))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

try:
    from .schemas import FusionInput, ModalitySignal, FusionOutput
    from .fusion import compute_fusion
    from .weights import FUSION_WEIGHTS
    from .adapters import (
        adapt_text_output,
        adapt_voice_output,
        adapt_behaviour_output,
        adapt_structured_output,
        adapt_temporal_output,
    )
except ImportError:
    from schemas import FusionInput, ModalitySignal, FusionOutput
    from fusion import compute_fusion
    from weights import FUSION_WEIGHTS
    from adapters import (
        adapt_text_output,
        adapt_voice_output,
        adapt_behaviour_output,
        adapt_structured_output,
        adapt_temporal_output,
    )



# ================================================================
# HELPERS
# ================================================================

def _make_input(
    patient_id="V0104",
    timestamp="2026-08-31T14:00:00",
    text=(True, 0.71),
    voice=(True, 0.16),
    behaviour=(True, 0.32),
    structured=(True, 0.69),
    temporal=(True, 0.78),
) -> FusionInput:
    """Shorthand to build a FusionInput from (available, risk) tuples."""
    def _sig(pair):
        avail, risk = pair
        return ModalitySignal(available=avail, risk=risk if avail else None)

    return FusionInput(
        patient_id=patient_id,
        timestamp=timestamp,
        text=_sig(text),
        voice=_sig(voice),
        behaviour=_sig(behaviour),
        structured=_sig(structured),
        temporal=_sig(temporal),
    )


# ================================================================
# TEST 1 — All five modalities available
# ================================================================

class TestAllAvailable:

    def test_fused_risk_formula(self):
        inp = _make_input()
        out = compute_fusion(inp)

        expected = (
            0.25 * 0.71
            + 0.15 * 0.16
            + 0.15 * 0.32
            + 0.25 * 0.69
            + 0.20 * 0.78
        )

        assert out.fusion_available is True
        assert out.fused_risk == pytest.approx(expected, abs=1e-4)

    def test_dds_equals_fused_risk_times_100(self):
        inp = _make_input()
        out = compute_fusion(inp)
        assert out.dds == pytest.approx(out.fused_risk * 100, abs=0.01)

    def test_effective_weights_equal_original_weights(self):
        inp = _make_input()
        out = compute_fusion(inp)
        for key in FUSION_WEIGHTS:
            assert out.effective_weights[key] == pytest.approx(
                FUSION_WEIGHTS[key], abs=1e-6
            )

    def test_future_escalation_present(self):
        inp = _make_input(temporal=(True, 0.78))
        out = compute_fusion(inp)
        assert isinstance(out.future_escalation, dict)
        assert out.future_escalation["risk"] == 0.78
        assert out.future_escalation["window_days"] == 7
        assert out.future_escalation["prediction"] == 1



# ================================================================
# TESTS 2–6 — Each modality individually missing
# ================================================================

@pytest.mark.parametrize("missing_key", [
    "voice",      # TEST 2
    "text",       # TEST 3
    "behaviour",  # TEST 4
    "structured", # TEST 5
    "temporal",   # TEST 6
])
class TestOneMissing:

    def test_fusion_still_available(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)
        assert out.fusion_available is True

    def test_future_escalation_missing(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)
        if missing_key == "temporal":
            assert out.future_escalation == "not_available"
        else:
            assert isinstance(out.future_escalation, dict)


    def test_missing_modality_weight_is_zero(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)
        assert out.effective_weights[missing_key] == 0.0

    def test_effective_weights_sum_to_one(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)
        total = sum(out.effective_weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_redistributed_weights_correct(self, missing_key):
        kwargs = {missing_key: (False, None)}
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)

        available_keys = [k for k in FUSION_WEIGHTS if k != missing_key]
        raw_sum = sum(FUSION_WEIGHTS[k] for k in available_keys)

        for key in available_keys:
            expected = FUSION_WEIGHTS[key] / raw_sum
            assert out.effective_weights[key] == pytest.approx(
                expected, abs=1e-6
            )


# ================================================================
# TEST 7 — Only one modality available
# ================================================================

@pytest.mark.parametrize("only_key,risk_val", [
    ("text", 0.50),
    ("voice", 0.30),
    ("behaviour", 0.80),
    ("structured", 0.60),
    ("temporal", 0.90),
])
class TestOnlyOneAvailable:

    def test_fused_risk_equals_that_modality(self, only_key, risk_val):
        kwargs = {
            "text": (False, None),
            "voice": (False, None),
            "behaviour": (False, None),
            "structured": (False, None),
            "temporal": (False, None),
        }
        kwargs[only_key] = (True, risk_val)
        inp = _make_input(**kwargs)
        out = compute_fusion(inp)

        assert out.fusion_available is True
        assert out.fused_risk == pytest.approx(risk_val, abs=1e-6)
        assert out.effective_weights[only_key] == pytest.approx(1.0, abs=1e-6)


# ================================================================
# TEST 8 — All modalities unavailable
# ================================================================

class TestAllUnavailable:

    def test_fusion_not_available(self):
        inp = _make_input(
            text=(False, None),
            voice=(False, None),
            behaviour=(False, None),
            structured=(False, None),
            temporal=(False, None),
        )
        out = compute_fusion(inp)

        assert out.fusion_available is False
        assert out.fused_risk is None
        assert out.dds is None

    def test_all_weights_zero(self):
        inp = _make_input(
            text=(False, None),
            voice=(False, None),
            behaviour=(False, None),
            structured=(False, None),
            temporal=(False, None),
        )
        out = compute_fusion(inp)

        for key in FUSION_WEIGHTS:
            assert out.effective_weights[key] == 0.0


# ================================================================
# TEST 9 — Effective weights sum to 1
# ================================================================

class TestWeightsIntegrity:

    @pytest.mark.parametrize("n_missing", [0, 1, 2, 3, 4])
    def test_weights_sum_to_one(self, n_missing):
        keys = list(FUSION_WEIGHTS.keys())
        kwargs = {}
        for i, key in enumerate(keys):
            if i < n_missing:
                kwargs[key] = (False, None)
            else:
                kwargs[key] = (True, 0.5)

        inp = _make_input(**kwargs)
        out = compute_fusion(inp)

        if out.fusion_available:
            total = sum(out.effective_weights.values())
            assert total == pytest.approx(1.0, abs=1e-6)


# ================================================================
# TEST 10 — Fused risk between 0 and 1
# ================================================================

class TestFusedRiskBounds:

    def test_all_zero_risks(self):
        inp = _make_input(
            text=(True, 0.0),
            voice=(True, 0.0),
            behaviour=(True, 0.0),
            structured=(True, 0.0),
            temporal=(True, 0.0),
        )
        out = compute_fusion(inp)
        assert out.fused_risk == pytest.approx(0.0, abs=1e-6)

    def test_all_one_risks(self):
        inp = _make_input(
            text=(True, 1.0),
            voice=(True, 1.0),
            behaviour=(True, 1.0),
            structured=(True, 1.0),
            temporal=(True, 1.0),
        )
        out = compute_fusion(inp)
        assert out.fused_risk == pytest.approx(1.0, abs=1e-6)

    def test_mixed_risks_in_bounds(self):
        inp = _make_input()
        out = compute_fusion(inp)
        assert 0.0 <= out.fused_risk <= 1.0


# ================================================================
# TEST 11 — DDS between 0 and 100
# ================================================================

class TestDDSBounds:

    def test_dds_at_zero(self):
        inp = _make_input(
            text=(True, 0.0),
            voice=(True, 0.0),
            behaviour=(True, 0.0),
            structured=(True, 0.0),
            temporal=(True, 0.0),
        )
        out = compute_fusion(inp)
        assert out.dds == pytest.approx(0.0, abs=0.01)

    def test_dds_at_hundred(self):
        inp = _make_input(
            text=(True, 1.0),
            voice=(True, 1.0),
            behaviour=(True, 1.0),
            structured=(True, 1.0),
            temporal=(True, 1.0),
        )
        out = compute_fusion(inp)
        assert out.dds == pytest.approx(100.0, abs=0.01)


# ================================================================
# TEST 12 — patient_id and timestamp passthrough
# ================================================================

class TestMetadataPassthrough:

    def test_patient_id_unchanged(self):
        inp = _make_input(patient_id="V9999")
        out = compute_fusion(inp)
        assert out.patient_id == "V9999"

    def test_timestamp_unchanged(self):
        ts = "2026-12-25T00:00:00"
        inp = _make_input(timestamp=ts)
        out = compute_fusion(inp)
        assert out.timestamp == ts


# ================================================================
# TEST 13 — Behaviour Risk formula
# ================================================================

class TestBehaviourAdapter:

    def test_normal_values(self):
        raw = {
            "anomaly_score": 0.80,
            "engagement_deviation": 1.5,
            "inactivity_score": 0.2,
        }
        sig = adapt_behaviour_output(raw)
        assert sig.available is True

        eng_norm = min(1.5 / 3.0, 1.0)  # 0.5
        expected = 0.40 * 0.80 + 0.30 * eng_norm + 0.30 * 0.2
        assert sig.risk == pytest.approx(expected, abs=1e-6)

    def test_high_engagement_deviation_clipped(self):
        raw = {
            "anomaly_score": 0.50,
            "engagement_deviation": 10.0,  # way above 3
            "inactivity_score": 0.0,
        }
        sig = adapt_behaviour_output(raw)
        eng_norm = 1.0  # clipped
        expected = 0.40 * 0.50 + 0.30 * eng_norm + 0.30 * 0.0
        assert sig.risk == pytest.approx(expected, abs=1e-6)

    def test_missing_anomaly_marks_unavailable(self):
        raw = {
            "anomaly_score": None,
            "engagement_deviation": 0.5,
            "inactivity_score": 0.1,
        }
        sig = adapt_behaviour_output(raw)
        assert sig.available is False

    def test_empty_dict_unavailable(self):
        sig = adapt_behaviour_output({})
        assert sig.available is False

    def test_none_input_unavailable(self):
        sig = adapt_behaviour_output(None)
        assert sig.available is False


# ================================================================
# TEST 14 — Text Risk formula
# ================================================================

class TestTextAdapter:

    def test_average_of_five_signals(self):
        raw = {
            "text_available": 1,
            "text_vector": {
                "text_distress": 0.80,
                "fear_signal": 0.60,
                "threat_context": 0.70,
                "negative_affect": 0.50,
                "urgency": 0.40,
            },
        }
        sig = adapt_text_output(raw)
        assert sig.available is True
        expected = (0.80 + 0.60 + 0.70 + 0.50 + 0.40) / 5
        assert sig.risk == pytest.approx(expected, abs=1e-6)

    def test_text_not_available(self):
        raw = {"text_available": 0, "text_vector": {}}
        sig = adapt_text_output(raw)
        assert sig.available is False

    def test_missing_signal_marks_unavailable(self):
        raw = {
            "text_available": 1,
            "text_vector": {
                "text_distress": 0.80,
                # missing others
            },
        }
        sig = adapt_text_output(raw)
        assert sig.available is False

    def test_none_input_unavailable(self):
        sig = adapt_text_output(None)
        assert sig.available is False


# ================================================================
# TEST 15 — GRU uses temporal_risk_score only
# ================================================================

class TestTemporalAdapter:

    def test_uses_temporal_risk_score(self):
        raw = {
            "temporal_risk_score": 0.83,
            "prediction": 1,
            "threshold_used": 0.15,
        }
        sig = adapt_temporal_output(raw)
        assert sig.available is True
        assert sig.risk == pytest.approx(0.83, abs=1e-6)

    def test_ignores_prediction_field(self):
        raw = {
            "temporal_risk_score": 0.10,
            "prediction": 1,  # should be ignored
            "threshold_used": 0.15,
        }
        sig = adapt_temporal_output(raw)
        assert sig.risk == pytest.approx(0.10, abs=1e-6)

    def test_missing_score_unavailable(self):
        raw = {"prediction": 1, "threshold_used": 0.15}
        sig = adapt_temporal_output(raw)
        assert sig.available is False

    def test_none_input_unavailable(self):
        sig = adapt_temporal_output(None)
        assert sig.available is False


# ================================================================
# TEST 16 — Voice uses voice_distress only
# ================================================================

class TestVoiceAdapter:

    def test_uses_voice_distress(self):
        raw = {
            "voice_available": True,
            "fusion_features": {
                "voice_available": 1,
                "voice_distress": 0.42,
                "pause_ratio": 0.1,
                "speech_rate_deviation": 0.5,
                "energy_deviation": 0.3,
                "acoustic_indicator": 0.6,
            },
        }
        sig = adapt_voice_output(raw)
        assert sig.available is True
        assert sig.risk == pytest.approx(0.42, abs=1e-6)

    def test_voice_not_available(self):
        raw = {
            "voice_available": False,
            "fusion_features": {
                "voice_available": 0,
                "voice_distress": None,
            },
        }
        sig = adapt_voice_output(raw)
        assert sig.available is False

    def test_none_input_unavailable(self):
        sig = adapt_voice_output(None)
        assert sig.available is False


# ================================================================
# TEST 17 — Structured adapter passthrough
# ================================================================

class TestStructuredAdapter:

    def test_passthrough_probability(self):
        raw = {
            "structured_available": True,
            "structured_risk": 0.76,
            "structured_flag": 1,
            "threshold": 0.16,
        }
        sig = adapt_structured_output(raw)
        assert sig.available is True
        assert sig.risk == pytest.approx(0.76, abs=1e-6)

    def test_not_available(self):
        raw = {"structured_available": False}
        sig = adapt_structured_output(raw)
        assert sig.available is False

    def test_none_input_unavailable(self):
        sig = adapt_structured_output(None)
        assert sig.available is False


# ================================================================
# TEST 18 — to_dict serialisation
# ================================================================

class TestSerialization:

    def test_to_dict_returns_plain_dict(self):
        inp = _make_input()
        out = compute_fusion(inp)
        d = out.to_dict()

        assert isinstance(d, dict)
        assert d["patient_id"] == "V0104"
        assert d["fusion_available"] is True
        assert isinstance(d["signals"], dict)
        assert isinstance(d["effective_weights"], dict)
        assert isinstance(d["fused_risk"], float)
        assert isinstance(d["dds"], float)


# ================================================================
# TEST 19 — End-to-end demo scenario (hero demo V0104)
# ================================================================

class TestHeroDemoScenario:
    """
    Simulates the V0104 hero demo at Day 28.
    """

    def test_v0104_day28(self):
        # Simulated engine outputs for V0104 Day 28
        text_out = {
            "text_available": 1,
            "text_vector": {
                "text_distress": 0.78,
                "fear_signal": 0.82,
                "threat_context": 0.69,
                "negative_affect": 0.65,
                "urgency": 0.71,
            },
        }
        voice_out = {
            "voice_available": False,
            "fusion_features": {
                "voice_available": 0,
                "voice_distress": None,
            },
        }
        behaviour_out = {
            "anomaly_score": 0.87,
            "engagement_deviation": 2.1,
            "inactivity_score": 0.33,
        }
        structured_out = {
            "structured_available": True,
            "structured_risk": 0.76,
        }
        temporal_out = {
            "temporal_risk_score": 0.83,
            "prediction": 1,
            "threshold_used": 0.15,
        }

        # Adapt
        text_sig = adapt_text_output(text_out)
        voice_sig = adapt_voice_output(voice_out)
        behav_sig = adapt_behaviour_output(behaviour_out)
        struct_sig = adapt_structured_output(structured_out)
        temp_sig = adapt_temporal_output(temporal_out)

        inp = FusionInput(
            patient_id="V0104",
            timestamp="2026-08-28T10:00:00",
            text=text_sig,
            voice=voice_sig,
            behaviour=behav_sig,
            structured=struct_sig,
            temporal=temp_sig,
        )

        out = compute_fusion(inp)

        # Voice is missing — should still produce fusion
        assert out.fusion_available is True
        assert out.availability["voice"] == 0
        assert out.effective_weights["voice"] == 0.0

        # Remaining weights redistributed over 0.85
        assert sum(out.effective_weights.values()) == pytest.approx(1.0, abs=1e-6)

        # Fused risk should be relatively high (hero demo scenario)
        assert out.fused_risk is not None
        assert out.fused_risk > 0.5
        assert 0.0 <= out.fused_risk <= 1.0

        # DDS should be high
        assert out.dds is not None
        assert out.dds > 50
        assert out.dds <= 100


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))

