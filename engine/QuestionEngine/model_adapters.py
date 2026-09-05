"""
model_adapters.py
=================
Thin adapter/converter functions for external model outputs → MEDHA State.

ADAPTER CONTRACT
----------------
Each adapter translates ONE model's output format into a partial MEDHA State
dict. That dict is then passed to MedhaState.update().

Adapters MUST:
  - Return a plain dict safe to pass to MedhaState.update().
  - Ignore unknown model keys (no crash).
  - Translate data only.

Adapters MUST NOT:
  - Select questions.
  - Change question priorities or cooldowns.
  - Apply clinical thresholds or diagnose conditions.
  - Decide emergency interventions.
  - Map model signals to QE triggers unless the mapping is an explicitly
    approved Question Engine policy (see POLICY MAPPINGS section below).

USAGE
-----
    from medha_state import MedhaState
    from model_adapters import (
        behaviour_signals_to_state,
        nlp_signals_to_state,
        longitudinal_signals_to_state,
        speech_signals_to_state,
    )

    state = MedhaState(scheduled_checkin_due=True)
    state.update(behaviour_signals_to_state(behaviour_output))
    state.update(nlp_signals_to_state(nlp_output))
    state.update(speech_signals_to_state(voice_engine_output))

    from test_engine import select_next_question
    question = select_next_question(state.to_dict(), history)

MODEL CONNECTION STATUS
-----------------------
  Behaviour Model  — interface ready; real model not yet connected
  NLP/Text Model   — interface ready; real model not yet connected (medha_nlp.py)
  Speech Model     — interface ready; Voice Engine schema normalised (Atharva, 2026-08-30)
  Structured Risk  — interface ready via structured_risk_adapter.py
  Longitudinal     — connected via patient_context.derive_question_engine_state()
"""


# ===========================================================================
# BEHAVIOUR MODEL ADAPTER
# ===========================================================================

# Mapping: Behaviour Model output key → QE state flag name.
# Only existing QE trigger flags are included. No new flags invented.
# Source: trigger_matches() in test_engine.py — every state key read there.
_BEHAVIOUR_KEY_MAP: dict = {
    "functioning_trend_declining":          "functioning_trend_declining",
    "two_consecutive_low_sleep":            "two_consecutive_low_sleep",
    "two_or_more_low_wellbeing":            "two_or_more_low_wellbeing",
    "support_network_change_or_SE01_drop":  "support_network_change_or_SE01_drop",
    "low_support_or_high_withdrawal_twice": "low_support_or_high_withdrawal_twice",
    "safety_intent_active":                 "safety_intent_active",
    "upcoming_or_recent_case_event":        "upcoming_or_recent_case_event",
    "previous_wellbeing_checkin_exists":    "previous_wellbeing_checkin_exists",
    "event_trigger_signal":                 "event_trigger_signal",
}


def behaviour_signals_to_state(behaviour_output: dict) -> dict:
    """
    Translate Behaviour Model output into a partial MEDHA State dict.

    Parameters
    ----------
    behaviour_output : dict
        Output from the Behaviour Model. Expected to contain any subset of
        the keys in _BEHAVIOUR_KEY_MAP. Unknown keys are ignored.

    Returns
    -------
    dict
        Partial MEDHA State dict. Safe to pass to MedhaState.update().
        Only recognised bool-valued trigger flags are included.

    Example
    -------
        behaviour_output = {"functioning_trend_declining": True}
        state.update(behaviour_signals_to_state(behaviour_output))
        # → state["functioning_trend_declining"] = True
        # → QE selects SF-05 (concentration/functioning question)

    Notes
    -----
    - The Behaviour Model is not yet connected. When it is delivered,
      it should produce a dict of the recognised flag names above.
    - Missing keys are not an error; they simply produce no update.
    - Non-bool values for flag keys are silently ignored.
    """
    if not isinstance(behaviour_output, dict):
        return {}

    partial: dict = {}
    for model_key, state_key in _BEHAVIOUR_KEY_MAP.items():
        if model_key in behaviour_output:
            value = behaviour_output[model_key]
            if isinstance(value, bool):
                partial[state_key] = value

    return partial


# ===========================================================================
# NLP / TEXT MODEL ADAPTER
# ===========================================================================

# NLP signal keys accepted from the NLP extraction schema.
# These are INFORMATIONAL — stored in patient_context["nlp_signals"].
# None of these directly activate a QE trigger in this adapter.
_NLP_INFORMATIONAL_KEYS: frozenset = frozenset({
    "mentioned_emotions",
    "mentioned_problems",
    "linked_case_event",
    "sleep_issue",
    "social_support_issue",
    "safety_concern_mentioned",
    "needs_human_followup",
    "confidence",
    "extraction_status",
    "raw_text",
})


def nlp_signals_to_state(nlp_output: dict) -> dict:
    """
    Translate NLP extraction output into a partial MEDHA State dict.

    NLP signals are INFORMATIONAL. They are stored in
    patient_context["nlp_signals"] so downstream components can inspect
    them (e.g. longitudinal analysis, human review queues).

    NO NLP field is automatically mapped to a Question Engine trigger flag
    in this function.

    If a policy decision is ever approved to promote a specific NLP signal
    to a QE trigger (for example, safety_concern_mentioned →
    safety_intent_active), that must be implemented as a SEPARATE, explicitly
    labelled policy function — not here, and only when formally approved as
    a Question Engine policy.

    Parameters
    ----------
    nlp_output : dict
        Output from nlp_interface.extract_free_text_signals() or a compatible
        NLP extraction dict. Unknown keys are ignored.

    Returns
    -------
    dict
        Partial MEDHA State dict containing:
            {"patient_context": {"nlp_signals": { ... }}}
        Safe to pass to MedhaState.update().
        Does NOT contain any QE trigger flag keys.

    Example
    -------
        nlp_out = {
            "mentioned_emotions": ["worried"],
            "sleep_issue": True,
            "safety_concern_mentioned": None,
            ...
        }
        state.update(nlp_signals_to_state(nlp_out))
        # → state._patient_context["nlp_signals"] = { ... }
        # → No QE trigger is activated by this call.
    """
    if not isinstance(nlp_output, dict):
        return {}

    nlp_signals: dict = {
        k: v for k, v in nlp_output.items()
        if k in _NLP_INFORMATIONAL_KEYS
    }

    if not nlp_signals:
        return {}

    return {
        "patient_context": {
            "nlp_signals": nlp_signals
        }
    }


# ===========================================================================
# SPEECH MODEL ADAPTER  — Voice Engine schema (Atharva, 2026-08-30)
# ===========================================================================

# Top-level scalar fields preserved from Voice Engine output.
_SPEECH_TOP_LEVEL_KEYS: frozenset = frozenset({
    "patient_id",
    "timestamp",
    "voice_available",
    "history_records",
})

# Nested dict fields whose contents are preserved verbatim.
# Keys: Voice Engine output key → stored-as key in speech_signals.
_SPEECH_NESTED_KEYS: tuple = (
    ("voice_features",   "voice_features"),
    ("fusion_features",  "fusion_features"),
    ("speech",           "speech"),
    ("raw_features",     "raw_features"),
)

# The 6 numeric features that Atharva's voice_features block always contains.
# Used by tests to verify preservation.
VOICE_FEATURE_FIELDS: frozenset = frozenset({
    "voice_distress",
    "voice_confidence",
    "pause_ratio",
    "speech_rate_deviation",
    "energy_deviation",
    "acoustic_indicator",
})


def speech_signals_to_state(speech_output: dict) -> dict:
    """
    Translate Voice Engine output into a partial MEDHA State dict.

    The Voice Engine (teammate: Atharva) produces a JSON payload with the
    following top-level schema (confirmed 2026-08-30)::

        {
            "patient_id":       str,
            "timestamp":        str  (ISO-8601),
            "voice_available":  bool,
            "voice_features": {
                "voice_distress":          float,   # 0–1
                "voice_confidence":        float,   # 0–1
                "pause_ratio":             float,
                "speech_rate_deviation":   float,
                "energy_deviation":        float,
                "acoustic_indicator":      float,
            },
            "fusion_features":  { ... },  # same 6 fields + voice_available int
            "speech": {
                "transcript":              str,
                "language":               str,
                "language_probability":   float,
                "speech_rate_wpm":        float,
            },
            "raw_features": {
                "emotion_probabilities":  { "neu", "hap", "ang", "sad" },
                "acoustic_features":      { ... },
            },
            "history_records":  int,
        }

    NORMALIZATION STRATEGY
    ----------------------
    All fields are stored verbatim inside::

        patient_context["speech_signals"][...]

    This is INFORMATIONAL only — no QE trigger flag is set here.
    If a policy decision is ever approved to promote a speech signal
    (e.g. voice_distress above a threshold → safety_intent_active), that
    mapping MUST be implemented as a separate, explicitly labelled policy
    function, never in this adapter.

    Parameters
    ----------
    speech_output : dict
        JSON payload from the Voice Engine.
        Unknown top-level keys are silently ignored.
        If voice_available is False or absent, the features sub-dicts may
        be absent; that is handled gracefully.

    Returns
    -------
    dict
        Partial MEDHA State dict::

            {
                "patient_context": {
                    "speech_signals": {
                        "patient_id":       ...,
                        "timestamp":        ...,
                        "voice_available":  ...,
                        "history_records":  ...,
                        "voice_features":   { ... },
                        "fusion_features":  { ... },
                        "speech":           { ... },
                        "raw_features":     { ... },
                    }
                }
            }

        Empty dict if speech_output is not a dict or is empty.
        Does NOT contain any QE trigger flag keys.

    Example
    -------
        voice_out = {
            "patient_id": "patient_001",
            "voice_available": True,
            "voice_features": {"voice_distress": 0.16, ...},
            ...
        }
        state.update(speech_signals_to_state(voice_out))
        # → state._patient_context["speech_signals"] = { ... }
        # → No QE trigger is activated by this call.
    """
    if not isinstance(speech_output, dict) or not speech_output:
        return {}

    speech_signals: dict = {}

    # Preserve recognised top-level scalars.
    for key in _SPEECH_TOP_LEVEL_KEYS:
        if key in speech_output:
            speech_signals[key] = speech_output[key]

    # Preserve recognised nested dicts verbatim.
    for src_key, dst_key in _SPEECH_NESTED_KEYS:
        if src_key in speech_output and isinstance(speech_output[src_key], dict):
            speech_signals[dst_key] = dict(speech_output[src_key])

    if not speech_signals:
        return {}

    return {
        "patient_context": {
            "speech_signals": speech_signals
        }
    }


# ===========================================================================
# LONGITUDINAL ADAPTER
# ===========================================================================

# The 4 flag names returned by derive_question_engine_state() that have
# explicit project-defined rules.
_LONGITUDINAL_KEYS: frozenset = frozenset({
    "previous_wellbeing_checkin_exists",
    "functioning_trend_declining",
    "support_network_change_or_SE01_drop",
    "safety_intent_active",
})


def longitudinal_signals_to_state(derived: dict) -> dict:
    """
    Translate the output of patient_context.derive_question_engine_state()
    into a partial MEDHA State dict.

    derive_question_engine_state() already uses the correct QE flag names,
    so this is a validated passthrough — it filters to the 4 flags that
    function is known to return and verifies they are booleans.

    Parameters
    ----------
    derived : dict
        Return value of derive_question_engine_state(patient_context,
        patient_history_rows).

    Returns
    -------
    dict
        Partial MEDHA State dict. Safe to pass to MedhaState.update().

    Example
    -------
        from patient_context import derive_question_engine_state
        derived = derive_question_engine_state(ctx, history_rows)
        state.update(longitudinal_signals_to_state(derived))
    """
    if not isinstance(derived, dict):
        return {}

    return {
        k: v for k, v in derived.items()
        if k in _LONGITUDINAL_KEYS and isinstance(v, bool)
    }


# ===========================================================================
# STRUCTURED RISK ENGINE ADAPTER
# ===========================================================================

from structured_risk_adapter import (
    REQUIRED_STRUCTURED_RISK_FIELDS,
    extract_structured_risk_payload,
    structured_risk_payload_to_state,
)
