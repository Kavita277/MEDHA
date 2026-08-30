"""
medha_state.py
==============
Common MEDHA State representation.

PURPOSE
-------
Provide a single, model-agnostic container for the state that the Question
Engine reads. External models populate it via model_adapters.py. The Question
Engine continues consuming a plain dict through its existing interface.

USAGE
-----
    from medha_state import MedhaState
    from model_adapters import behaviour_signals_to_state, nlp_signals_to_state

    state = MedhaState(scheduled_checkin_due=True)
    state.update(behaviour_signals_to_state(behaviour_output))
    state.update(nlp_signals_to_state(nlp_output))

    question = select_next_question(state.to_dict(), history)

DESIGN PRINCIPLES
-----------------
- Pure data container. Zero question-selection logic.
- All trigger flags default to the safe "inactive" value (False).
- Unknown keys are collected in _unknown and never reach the Question Engine.
- No clinical decisions. No thresholds. No model-specific assumptions.

QUESTION ENGINE INTERFACE
-------------------------
The Question Engine calls:
    select_next_question(state_dict, history)

where state_dict is exactly what MedhaState.to_dict() returns.
The QE is NOT aware of MedhaState — it still receives a plain dict.
No changes to the Question Engine are required.
"""

# ---------------------------------------------------------------------------
# Complete inventory of QE trigger flags and their safe defaults.
# Source: trigger_matches() in test_engine.py — every state key read there.
# ---------------------------------------------------------------------------

_QE_TRIGGER_DEFAULTS: dict = {
    # Scheduling
    "scheduled_checkin_due":                False,
    "low_frequency_checkin_due":            False,
    "scheduled_safety_check_due":           False,
    "scheduled_safety_support_check_due":   False,

    # Safety (Priority 1) — SA-01, SA-02
    "safety_intent_active":                 False,

    # Event (Priority 2) — ES-01, ES-02
    "upcoming_or_recent_case_event":        False,
    "event_trigger_signal":                 False,

    # Sleep / Functioning (Priority 3) — SF-03, SF-05
    "two_consecutive_low_sleep":            False,
    "functioning_trend_declining":          False,

    # Social Support (Priority 3) — SE-03, SE-06
    "support_network_change_or_SE01_drop":  False,
    "low_support_or_high_withdrawal_twice": False,

    # General Wellbeing (Priority 4) — GW-05, GW-06
    "previous_wellbeing_checkin_exists":    False,
    "two_or_more_low_wellbeing":            False,
}

# Keys the QE state dict may contain (triggers + patient_context)
_KNOWN_STATE_KEYS: frozenset = frozenset(_QE_TRIGGER_DEFAULTS) | {"patient_context"}


class MedhaState:
    """
    Common container for MEDHA Question Engine state.

    Parameters
    ----------
    **overrides : keyword arguments
        Any subset of the recognised QE trigger flags or patient_context.
        Unknown keys are silently stored in _unknown and never forwarded
        to the Question Engine.

    Examples
    --------
    Minimal session state:
        state = MedhaState(scheduled_checkin_due=True)

    Session with a safety signal:
        state = MedhaState(
            scheduled_checkin_due=True,
            safety_intent_active=True,
        )

    Merge model output:
        state = MedhaState(scheduled_checkin_due=True)
        state.update(behaviour_signals_to_state(behaviour_output))
        question = select_next_question(state.to_dict(), history)
    """

    def __init__(self, **overrides):
        # Mutable copy of defaults — one per instance.
        self._triggers: dict = dict(_QE_TRIGGER_DEFAULTS)
        # patient_context is kept separate to allow nested merges.
        self._patient_context: dict = {"events": {}}
        # Unknown keys stored here, never forwarded to the QE.
        self._unknown: dict = {}

        if overrides:
            self._apply(overrides)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply(self, signals: dict) -> None:
        """Merge a signals dict into the appropriate internal stores."""
        for key, value in signals.items():
            if key in _QE_TRIGGER_DEFAULTS:
                # Only accept proper booleans for trigger flags.
                if isinstance(value, bool):
                    self._triggers[key] = value
                else:
                    # Record the unexpected type without crashing.
                    self._unknown[f"{key}__type_error"] = (
                        f"expected bool, got {type(value).__name__}: {value!r}"
                    )
            elif key == "patient_context":
                if isinstance(value, dict):
                    # Deep-merge: update sub-keys, not replace the whole dict.
                    self._merge_patient_context(value)
                else:
                    self._unknown["patient_context__type_error"] = (
                        f"expected dict, got {type(value).__name__}"
                    )
            else:
                # Unknown key — stored for diagnostics only.
                self._unknown[key] = value

    def _merge_patient_context(self, incoming: dict) -> None:
        """Merge incoming patient_context sub-keys into self._patient_context."""
        for k, v in incoming.items():
            if k == "events" and isinstance(v, dict):
                existing = self._patient_context.get("events", {})
                existing.update(v)
                self._patient_context["events"] = existing
            else:
                self._patient_context[k] = v

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, signals: dict) -> "MedhaState":
        """
        Merge a partial state dict into this MedhaState.

        Parameters
        ----------
        signals : dict
            Typically the return value of an adapter function, e.g.:
                behaviour_signals_to_state(behaviour_output)
                nlp_signals_to_state(nlp_output)

        Returns self to allow chaining.

        Unknown keys are silently stored in .unknown_keys, not forwarded
        to the Question Engine.
        """
        if isinstance(signals, dict):
            self._apply(signals)
        return self

    def to_dict(self) -> dict:
        """
        Return the flat state dict that select_next_question() expects.

        This is the ONLY method the Question Engine caller needs.
        The QE is not aware of MedhaState — it receives a plain dict.
        """
        result: dict = dict(self._triggers)
        result["patient_context"] = dict(self._patient_context)
        return result

    @property
    def unknown_keys(self) -> dict:
        """
        Signals that were received but are not recognised QE state keys.

        Available for diagnostics and logging. Never forwarded to the QE.
        """
        return dict(self._unknown)

    def __repr__(self) -> str:  # pragma: no cover
        active = {k: v for k, v in self._triggers.items() if v}
        return (
            f"MedhaState(active_triggers={list(active.keys())}, "
            f"unknown_keys={list(self._unknown.keys())})"
        )
