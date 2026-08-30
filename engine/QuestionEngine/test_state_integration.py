"""
test_state_integration.py
=========================
Integration tests for the MEDHA State interface and model adapters.

Tests covered
-------------
1  Behaviour output (functioning_trend_declining=True)
        → behaviour_signals_to_state()
        → MedhaState
        → select_next_question()
        → SF-05 selected

2  Explicit safety signal (safety_intent_active=True) via MedhaState
        → select_next_question()
        → SA-01 selected (existing safety mechanism, no new policy)

3  No actionable trigger, empty history
        → MedhaState (only scheduled_checkin_due=True)
        → select_next_question()
        → GW-01 (routine fallback)

4  Missing / unknown fields in Behaviour output
        → behaviour_signals_to_state()
        → MedhaState.update() does not crash
        → select_next_question() runs cleanly

5  NLP output enters the common state representation
        → nlp_signals_to_state()
        → MedhaState.update()
        → signals stored in patient_context["nlp_signals"]
        → NO QE trigger activated by the adapter
        → select_next_question() runs without crash

6  Voice Engine output (real payloads from Atharva, 2026-08-30)
        → speech_signals_to_state()
        → MedhaState.update()
        → all 6 voice_features fields preserved verbatim
        → transcript, language, speech_rate_wpm preserved
        → NO QE trigger activated by the adapter
        → select_next_question() runs without crash
        → Both payloads tested independently

Design notes
------------
- Does NOT load the Excel dataset.
- Does NOT require any real teammate model (Behaviour, Speech, NLP).
- Uses controlled test dicts only; Test 6 uses verbatim Voice Engine outputs.
- The QE interface (select_next_question) is called through the existing
  import — its logic is not modified.
- Existing tests T1–T10b and A–G are NOT duplicated here.
"""

import unittest

from medha_state import MedhaState
from model_adapters import (
    behaviour_signals_to_state,
    nlp_signals_to_state,
    longitudinal_signals_to_state,
    speech_signals_to_state,
    VOICE_FEATURE_FIELDS,
)
from test_engine import select_next_question


# ---------------------------------------------------------------------------
# Base state used across tests: only scheduled_checkin is active.
# No adaptive triggers, no safety, no events.
# ---------------------------------------------------------------------------

def _base_state(**overrides) -> MedhaState:
    """
    Return a MedhaState with scheduled_checkin_due=True and all other
    triggers False, then apply any overrides.
    """
    state = MedhaState(scheduled_checkin_due=True)
    for k, v in overrides.items():
        state.update({k: v})
    return state


# ===========================================================================
# Test 1 — Behaviour output → functioning_trend_declining → SF-05
# ===========================================================================

class Test1_BehaviourToFunctioningQuestion(unittest.TestCase):

    def test_behaviour_declining_functioning_selects_SF05(self):
        """
        A Behaviour Model output indicating declining functioning must result
        in the QE selecting SF-05 (concentration/functioning question).

        Flow:
            behaviour_output = {"functioning_trend_declining": True}
                ↓
            behaviour_signals_to_state()
                ↓
            MedhaState.update()
                ↓
            select_next_question()
                ↓
            SF-05
        """
        behaviour_output = {"functioning_trend_declining": True}

        state = _base_state()
        state.update(behaviour_signals_to_state(behaviour_output))

        state_dict = state.to_dict()

        # Verify the flag reached the state dict.
        self.assertTrue(
            state_dict["functioning_trend_declining"],
            "functioning_trend_declining must be True in QE state dict"
        )

        question = select_next_question(state_dict, [])

        self.assertIsNotNone(question, "QE must return a question")
        self.assertEqual(
            question["question_id"], "SF-05",
            f"Expected SF-05, got {question['question_id']}"
        )

    def test_behaviour_adapter_ignores_unknown_keys(self):
        """
        Extra keys in the Behaviour output that are not recognised QE flags
        must be silently ignored — not crash, not appear in the state dict.
        """
        behaviour_output = {
            "functioning_trend_declining": True,
            "some_future_model_field": "value",   # unknown
            "another_unknown": 42,                # unknown
        }

        partial = behaviour_signals_to_state(behaviour_output)

        # Only the known flag is in the partial dict.
        self.assertIn("functioning_trend_declining", partial)
        self.assertNotIn("some_future_model_field", partial)
        self.assertNotIn("another_unknown", partial)


# ===========================================================================
# Test 2 — Explicit safety signal → SA-01
# ===========================================================================

class Test2_SafetySignalToSafetyQuestion(unittest.TestCase):

    def test_safety_intent_active_selects_SA01(self):
        """
        When safety_intent_active=True is present in MEDHA State, the QE must
        select SA-01 (the highest-priority safety question).

        The safety flag is supplied explicitly — this uses the EXISTING
        safety selection mechanism in the QE (Priority 1, trigger
        "safety_intent_active"). No new policy is introduced.

        Note: safety_concern_mentioned (from NLP) is NOT automatically mapped
        to safety_intent_active. Any such mapping would require a separate,
        explicitly approved policy function.
        """
        state = _base_state(safety_intent_active=True)
        state_dict = state.to_dict()

        self.assertTrue(state_dict["safety_intent_active"])

        question = select_next_question(state_dict, [])

        self.assertIsNotNone(question)
        self.assertEqual(
            question["question_id"], "SA-01",
            f"Expected SA-01, got {question['question_id']}"
        )
        self.assertEqual(question["intent"], "safety_support")

    def test_safety_beats_event_trigger(self):
        """
        Safety (Priority 1) must beat an event trigger (Priority 2)
        when both are active — using the existing QE priority ordering.
        """
        state = _base_state(
            safety_intent_active=True,
            upcoming_or_recent_case_event=True,
            patient_context={"events": {"Upcoming_Hearing": 1}},
        )

        question = select_next_question(state.to_dict(), [])

        self.assertIsNotNone(question)
        self.assertEqual(
            question["question_id"], "SA-01",
            "Safety must beat event trigger"
        )


# ===========================================================================
# Test 3 — No trigger → GW-01 routine fallback
# ===========================================================================

class Test3_NoTriggerRoutineFallback(unittest.TestCase):

    def test_no_trigger_empty_history_gives_GW01(self):
        """
        When no adaptive trigger is active and history is empty, the QE must
        fall back to the routine scheduled_checkin path and select GW-01.
        """
        state = MedhaState(scheduled_checkin_due=True)
        # All other flags remain at their False defaults.

        question = select_next_question(state.to_dict(), [])

        self.assertIsNotNone(question)
        self.assertEqual(
            question["question_id"], "GW-01",
            f"Expected GW-01 (routine fallback), got {question['question_id']}"
        )

    def test_state_to_dict_has_all_required_keys(self):
        """
        MedhaState.to_dict() must produce all trigger keys the QE expects,
        even when no overrides are given.
        """
        from medha_state import _QE_TRIGGER_DEFAULTS

        state = MedhaState()
        state_dict = state.to_dict()

        for key in _QE_TRIGGER_DEFAULTS:
            self.assertIn(
                key, state_dict,
                f"Missing expected QE state key: {key}"
            )
        self.assertIn("patient_context", state_dict)


# ===========================================================================
# Test 4 — Missing / unknown model fields → no crash
# ===========================================================================

class Test4_UnknownFieldsSafety(unittest.TestCase):

    def test_empty_behaviour_output_does_not_crash(self):
        """An empty Behaviour output must produce an empty partial dict."""
        partial = behaviour_signals_to_state({})
        self.assertEqual(partial, {})

    def test_non_dict_behaviour_output_does_not_crash(self):
        """Non-dict Behaviour output must return empty dict without raising."""
        for bad_value in [None, "text", 42, [], True]:
            partial = behaviour_signals_to_state(bad_value)
            self.assertEqual(
                partial, {},
                f"Expected empty dict for input {bad_value!r}"
            )

    def test_all_unknown_keys_ignored_by_adapter(self):
        """All-unknown Behaviour output must produce empty partial dict."""
        behaviour_output = {
            "invented_field_a": True,
            "invented_field_b": "value",
            "invented_field_c": 99,
        }
        partial = behaviour_signals_to_state(behaviour_output)
        self.assertEqual(partial, {})

    def test_unknown_keys_stored_in_medha_state_unknown(self):
        """
        Unknown keys passed directly to MedhaState.update() must be stored
        in .unknown_keys and must NOT appear in .to_dict().
        """
        state = MedhaState(scheduled_checkin_due=True)
        state.update({
            "invented_model_field": True,
            "another_unknown": "value",
        })

        state_dict = state.to_dict()
        self.assertNotIn("invented_model_field", state_dict)
        self.assertNotIn("another_unknown", state_dict)

        self.assertIn("invented_model_field", state.unknown_keys)
        self.assertIn("another_unknown", state.unknown_keys)

    def test_qe_runs_cleanly_with_unknown_model_fields(self):
        """
        Unknown model output must not prevent the QE from selecting a question.
        """
        state = MedhaState(scheduled_checkin_due=True)
        state.update(behaviour_signals_to_state({
            "unknown_behaviour_field": True,
            "another_unknown": "value",
        }))

        # QE must still produce a valid question (routine fallback).
        question = select_next_question(state.to_dict(), [])
        self.assertIsNotNone(question)

    def test_non_bool_trigger_value_ignored(self):
        """
        A non-bool value for a recognised trigger key must be silently ignored.
        The flag must remain at its default (False).
        """
        state = MedhaState()
        state.update({"functioning_trend_declining": "yes"})  # wrong type

        state_dict = state.to_dict()
        self.assertFalse(
            state_dict["functioning_trend_declining"],
            "Non-bool trigger value must not update the flag"
        )
        # The type error is recorded in unknown_keys for diagnostics.
        self.assertIn(
            "functioning_trend_declining__type_error",
            state.unknown_keys
        )


# ===========================================================================
# Test 5 — NLP output enters the common state representation
# ===========================================================================

class Test5_NLPSignalsIntoState(unittest.TestCase):

    def test_nlp_signals_stored_in_patient_context(self):
        """
        NLP extraction output must be stored in
        patient_context["nlp_signals"] via nlp_signals_to_state().

        The adapter does NOT activate any QE trigger.
        """
        nlp_output = {
            "mentioned_emotions":       ["worried", "scared"],
            "mentioned_problems":       ["difficulty sleeping"],
            "linked_case_event":        "hearing",
            "sleep_issue":              True,
            "social_support_issue":     None,
            "safety_concern_mentioned": None,   # not True — no trigger should fire
            "needs_human_followup":     None,
            "confidence":               0.82,
        }

        state = _base_state()
        state.update(nlp_signals_to_state(nlp_output))

        state_dict = state.to_dict()

        # NLP signals must be in patient_context.
        self.assertIn(
            "nlp_signals", state_dict["patient_context"],
            "nlp_signals must be stored in patient_context"
        )
        stored = state_dict["patient_context"]["nlp_signals"]
        self.assertEqual(stored["mentioned_emotions"], ["worried", "scared"])
        self.assertEqual(stored["sleep_issue"], True)
        self.assertEqual(stored["confidence"], 0.82)

    def test_nlp_adapter_does_not_activate_any_qe_trigger(self):
        """
        nlp_signals_to_state() must NOT set any QE trigger flag,
        even when the NLP output contains safety_concern_mentioned=True.

        Mapping NLP signals to QE triggers is a separate policy decision
        that requires explicit approval and a separate labelled function.
        """
        from medha_state import _QE_TRIGGER_DEFAULTS

        nlp_output_with_safety = {
            "mentioned_emotions":       ["terrified"],
            "mentioned_problems":       ["being followed"],
            "linked_case_event":        None,
            "sleep_issue":              None,
            "social_support_issue":     None,
            "safety_concern_mentioned": True,   # NLP extracted this explicitly
            "needs_human_followup":     True,
            "confidence":               0.91,
        }

        partial = nlp_signals_to_state(nlp_output_with_safety)

        # No QE trigger flag must appear in the adapter's return value.
        for trigger_key in _QE_TRIGGER_DEFAULTS:
            self.assertNotIn(
                trigger_key, partial,
                f"Adapter must not set QE trigger '{trigger_key}'"
            )

        # The partial dict must only contain patient_context.
        self.assertIn("patient_context", partial)
        self.assertEqual(set(partial.keys()), {"patient_context"})

    def test_qe_runs_cleanly_after_nlp_update(self):
        """
        select_next_question() must run without error after NLP signals
        are merged into MEDHA State via nlp_signals_to_state().
        """
        nlp_output = {
            "mentioned_emotions": ["anxious"],
            "mentioned_problems": [],
            "linked_case_event":  None,
            "sleep_issue":        None,
            "social_support_issue": None,
            "safety_concern_mentioned": None,
            "needs_human_followup": None,
            "confidence": 0.75,
        }

        state = _base_state()
        state.update(nlp_signals_to_state(nlp_output))

        question = select_next_question(state.to_dict(), [])
        self.assertIsNotNone(question)

    def test_nlp_and_behaviour_signals_coexist(self):
        """
        Merging both NLP signals and Behaviour signals into MedhaState must
        work correctly: Behaviour flags activate QE triggers, NLP signals
        are stored informatively, no conflict between them.
        """
        nlp_output = {
            "mentioned_emotions": ["exhausted"],
            "mentioned_problems": ["sleep"],
            "linked_case_event":  None,
            "sleep_issue":        True,
            "social_support_issue": None,
            "safety_concern_mentioned": None,
            "needs_human_followup": None,
            "confidence": 0.7,
        }
        behaviour_output = {
            "functioning_trend_declining": True,
        }

        state = _base_state()
        state.update(nlp_signals_to_state(nlp_output))
        state.update(behaviour_signals_to_state(behaviour_output))

        state_dict = state.to_dict()

        # Behaviour flag activated.
        self.assertTrue(state_dict["functioning_trend_declining"])
        # NLP signals stored.
        self.assertIn("nlp_signals", state_dict["patient_context"])
        # QE selects functioning question.
        question = select_next_question(state_dict, [])
        self.assertEqual(question["question_id"], "SF-05")


# ===========================================================================
# Bonus — longitudinal and speech adapter smoke tests
# ===========================================================================

class TestAdapterSmoke(unittest.TestCase):

    def test_longitudinal_passthrough(self):
        """longitudinal_signals_to_state passes the 4 known flags through."""
        derived = {
            "previous_wellbeing_checkin_exists":   True,
            "functioning_trend_declining":         False,
            "support_network_change_or_SE01_drop": True,
            "safety_intent_active":                False,
        }
        partial = longitudinal_signals_to_state(derived)
        self.assertEqual(partial["previous_wellbeing_checkin_exists"], True)
        self.assertEqual(partial["support_network_change_or_SE01_drop"], True)
        self.assertNotIn("unknown_field", partial)

    def test_speech_unknown_only_keys_returns_empty(self):
        """
        A dict with ONLY unrecognised top-level keys (no nested dicts that
        match the schema) must return empty dict — nothing to preserve.
        """
        result = speech_signals_to_state({"distress_detected": True})
        self.assertEqual(result, {})

    def test_speech_does_not_crash_on_bad_input(self):
        """speech_signals_to_state must not raise for any non-dict input."""
        for bad in [None, [], "text", 99]:
            result = speech_signals_to_state(bad)
            self.assertEqual(result, {})

    def test_speech_empty_dict_returns_empty(self):
        """An empty dict must return an empty dict (nothing to preserve)."""
        self.assertEqual(speech_signals_to_state({}), {})


# ===========================================================================
# Test 6 — Voice Engine real payloads (Atharva, 2026-08-30)
# ===========================================================================

# ---------------------------------------------------------------------------
# Verbatim payloads from the Voice Engine teammate.
# DO NOT modify these dicts — they are the real model outputs used as
# integration-test fixtures. Normalisation happens inside the adapter.
# ---------------------------------------------------------------------------

_VOICE_PAYLOAD_1 = {
    "patient_id": "patient_001",
    "timestamp": "2026-08-30T10:41:02.754967",
    "voice_available": True,
    "voice_features": {
        "voice_distress": 0.1605,
        "voice_confidence": 0.7413,
        "pause_ratio": 0,
        "speech_rate_deviation": 0.4667,
        "energy_deviation": 0.317,
        "acoustic_indicator": 0.4375,
    },
    "fusion_features": {
        "voice_available": 1,
        "voice_distress": 0.1605,
        "pause_ratio": 0,
        "speech_rate_deviation": 0.4667,
        "energy_deviation": 0.317,
        "acoustic_indicator": 0.4375,
    },
    "speech": {
        "transcript": "You did.",
        "language": "en",
        "language_probability": 0.9674,
        "speech_rate_wpm": 80,
    },
    "raw_features": {
        "emotion_probabilities": {
            "neu": 0.0378,
            "hap": 0.7413,
            "ang": 0.2199,
            "sad": 0.001,
        },
        "acoustic_features": {
            "duration_seconds": 1.5,
            "rms_energy": 0.01366,
            "pitch_mean": 400.21,
            "pitch_std": 266.28,
            "zero_crossing_rate": 0.09227,
        },
    },
    "history_records": 2,
}

_VOICE_PAYLOAD_2 = {
    "patient_id": "patient_001",
    "timestamp": "2026-08-30T10:47:45.403525",
    "voice_available": True,
    "voice_features": {
        "voice_distress": 0.0523,
        "voice_confidence": 0.5114,
        "pause_ratio": 0,
        "speech_rate_deviation": 0.5897,
        "energy_deviation": 0.6058,
        "acoustic_indicator": 0.2356,
    },
    "fusion_features": {
        "voice_available": 1,
        "voice_distress": 0.0523,
        "pause_ratio": 0,
        "speech_rate_deviation": 0.5897,
        "energy_deviation": 0.6058,
        "acoustic_indicator": 0.2356,
    },
    "speech": {
        "transcript": "Excuse me?",
        "language": "en",
        "language_probability": 0.8371,
        "speech_rate_wpm": 61.54,
    },
    "raw_features": {
        "emotion_probabilities": {
            "neu": 0.4846,
            "hap": 0.5114,
            "ang": 0.0001,
            "sad": 0.0038,
        },
        "acoustic_features": {
            "duration_seconds": 1.95,
            "rms_energy": 0.00788,
            "pitch_mean": 255.61,
            "pitch_std": 76.32,
            "zero_crossing_rate": 0.10888,
        },
    },
    "history_records": 4,
}


class Test6_SpeechSignalsFromVoiceEngine(unittest.TestCase):
    """
    Integration tests using verbatim Voice Engine outputs from Atharva
    (2026-08-30).  The adapter must normalise the schema without modifying
    any values and without activating any QE trigger.
    """

    # -- Payload 1: "You did." (voice_distress=0.1605, hap=0.7413) -----------

    def test_payload1_stored_in_speech_signals(self):
        """
        Payload 1 must be stored inside patient_context["speech_signals"].
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_1))
        state_dict = state.to_dict()

        self.assertIn("speech_signals", state_dict["patient_context"],
                      "speech_signals must appear in patient_context")

    def test_payload1_all_six_voice_features_preserved(self):
        """
        All 6 voice_features fields must be stored with their exact float
        values — the adapter must not round, clip, or rename them.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_1))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertIn("voice_features", stored)
        vf = stored["voice_features"]
        for field in VOICE_FEATURE_FIELDS:
            self.assertIn(field, vf, f"voice_features.{field} must be preserved")

        self.assertAlmostEqual(vf["voice_distress"],        0.1605, places=4)
        self.assertAlmostEqual(vf["voice_confidence"],      0.7413, places=4)
        self.assertAlmostEqual(vf["pause_ratio"],           0.0,    places=4)
        self.assertAlmostEqual(vf["speech_rate_deviation"], 0.4667, places=4)
        self.assertAlmostEqual(vf["energy_deviation"],      0.317,  places=3)
        self.assertAlmostEqual(vf["acoustic_indicator"],    0.4375, places=4)

    def test_payload1_speech_block_preserved(self):
        """
        The speech transcript, language, and speech_rate_wpm from Payload 1
        must be preserved verbatim.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_1))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertIn("speech", stored)
        sp = stored["speech"]
        self.assertEqual(sp["transcript"],    "You did.")
        self.assertEqual(sp["language"],      "en")
        self.assertAlmostEqual(sp["speech_rate_wpm"], 80, places=1)

    def test_payload1_does_not_activate_any_qe_trigger(self):
        """
        Payload 1 must NOT set any QE trigger flag — voice signals are
        informational only until a policy mapping is formally approved.
        """
        from medha_state import _QE_TRIGGER_DEFAULTS

        partial = speech_signals_to_state(_VOICE_PAYLOAD_1)

        for trigger_key in _QE_TRIGGER_DEFAULTS:
            self.assertNotIn(
                trigger_key, partial,
                f"Adapter must not set QE trigger '{trigger_key}'"
            )
        self.assertEqual(set(partial.keys()), {"patient_context"})

    def test_payload1_qe_runs_cleanly(self):
        """
        select_next_question() must run without error after Payload 1 is
        merged into MEDHA State and return the routine fallback (GW-01).
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_1))

        question = select_next_question(state.to_dict(), [])
        self.assertIsNotNone(question)
        self.assertEqual(question["question_id"], "GW-01")

    # -- Payload 2: "Excuse me?" (voice_distress=0.0523, hap=0.5114) ---------

    def test_payload2_all_six_voice_features_preserved(self):
        """
        All 6 voice_features fields must be stored with their exact float
        values from Payload 2.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_2))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertIn("voice_features", stored)
        vf = stored["voice_features"]
        for field in VOICE_FEATURE_FIELDS:
            self.assertIn(field, vf, f"voice_features.{field} must be preserved")

        self.assertAlmostEqual(vf["voice_distress"],        0.0523, places=4)
        self.assertAlmostEqual(vf["voice_confidence"],      0.5114, places=4)
        self.assertAlmostEqual(vf["pause_ratio"],           0.0,    places=4)
        self.assertAlmostEqual(vf["speech_rate_deviation"], 0.5897, places=4)
        self.assertAlmostEqual(vf["energy_deviation"],      0.6058, places=4)
        self.assertAlmostEqual(vf["acoustic_indicator"],    0.2356, places=4)

    def test_payload2_speech_block_preserved(self):
        """
        Payload 2 transcript and speech_rate_wpm must be preserved verbatim.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_2))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        sp = stored["speech"]
        self.assertEqual(sp["transcript"],       "Excuse me?")
        self.assertAlmostEqual(sp["speech_rate_wpm"], 61.54, places=2)
        self.assertAlmostEqual(sp["language_probability"], 0.8371, places=4)

    def test_payload2_history_records_preserved(self):
        """
        The history_records scalar (4) from Payload 2 must be stored.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_2))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertEqual(stored.get("history_records"), 4)

    def test_payload2_raw_features_preserved(self):
        """
        The raw_features dict (emotion_probabilities + acoustic_features)
        from Payload 2 must be stored verbatim.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_2))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertIn("raw_features", stored)
        rf = stored["raw_features"]
        self.assertIn("emotion_probabilities", rf)
        self.assertAlmostEqual(rf["emotion_probabilities"]["hap"], 0.5114, places=4)
        self.assertIn("acoustic_features", rf)
        self.assertAlmostEqual(
            rf["acoustic_features"]["duration_seconds"], 1.95, places=2
        )

    def test_payload2_does_not_activate_any_qe_trigger(self):
        """
        Payload 2 must also NOT set any QE trigger flag.
        """
        from medha_state import _QE_TRIGGER_DEFAULTS

        partial = speech_signals_to_state(_VOICE_PAYLOAD_2)

        for trigger_key in _QE_TRIGGER_DEFAULTS:
            self.assertNotIn(trigger_key, partial)
        self.assertEqual(set(partial.keys()), {"patient_context"})

    def test_speech_and_behaviour_signals_coexist(self):
        """
        Merging Payload 2 (speech) and a Behaviour signal into MedhaState
        must work correctly: speech stored informatively, behaviour flag
        activates QE trigger, QE selects the correct question.
        """
        state = _base_state()
        state.update(speech_signals_to_state(_VOICE_PAYLOAD_2))
        state.update(behaviour_signals_to_state(
            {"functioning_trend_declining": True}
        ))

        state_dict = state.to_dict()

        # Behaviour flag activated.
        self.assertTrue(state_dict["functioning_trend_declining"])
        # Speech signals stored.
        self.assertIn("speech_signals", state_dict["patient_context"])
        # QE selects functioning question.
        question = select_next_question(state_dict, [])
        self.assertEqual(question["question_id"], "SF-05")

    def test_adapter_ignores_unknown_top_level_keys(self):
        """
        Extra top-level keys not in the schema (e.g. a future field the
        Voice Engine adds) must be silently ignored.
        """
        payload_with_extras = dict(_VOICE_PAYLOAD_1)
        payload_with_extras["future_field"] = "some_value"
        payload_with_extras["another_new_metric"] = 0.99

        state = _base_state()
        state.update(speech_signals_to_state(payload_with_extras))
        stored = state.to_dict()["patient_context"]["speech_signals"]

        self.assertNotIn("future_field", stored)
        self.assertNotIn("another_new_metric", stored)
        # Known fields still present.
        self.assertIn("voice_features", stored)
        self.assertIn("speech", stored)


# ===========================================================================
# Runner
# ===========================================================================

def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        Test1_BehaviourToFunctioningQuestion,
        Test2_SafetySignalToSafetyQuestion,
        Test3_NoTriggerRoutineFallback,
        Test4_UnknownFieldsSafety,
        Test5_NLPSignalsIntoState,
        TestAdapterSmoke,
        Test6_SpeechSignalsFromVoiceEngine,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 62)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passed = total - failures
    print(f"MEDHA STATE INTEGRATION TESTS: {passed} passed, {failures} failed"
          f"  (of {total} total)")
    print("=" * 62)
    return result


if __name__ == "__main__":
    run_tests()
