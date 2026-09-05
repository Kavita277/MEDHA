"""
structured_risk_adapter.py
===========================
Question Engine -> Structured Risk Engine raw-input adapter.

PURPOSE
-------
Extract and normalize the 7 Structured Risk Engine input fields from Question
Engine state, patient context, and session interaction records:
    1. Mood
    2. Stress
    3. Sleep
    4. Functioning
    5. Safety
    6. Social_Support_Checkin
    7. Self_Reported_Wellbeing

DESIGN PRINCIPLES
-----------------
- Pure adapter layer: zero question-selection or clinical/model logic changes.
- All 7 required fields are ALWAYS present in the output dictionary.
- If a field is unavailable or unanswered, its value is preserved as None.
  Values are NEVER invented.
- Supports extraction from:
    (a) patient_context dict (loaded via patient_context.load_patient_context)
    (b) live session interaction records (history.json or in-memory interaction list)
    (c) full MedhaState / state dict
- Does not modify any internal QE naming or behavior.
"""

from __future__ import annotations
from typing import Any

# Exact 7 required Structured Risk Engine field names
REQUIRED_STRUCTURED_RISK_FIELDS: tuple[str, ...] = (
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
)

# Mapping from question-level structured outputs to Structured Risk fields
_QUESTION_ANSWER_FIELD_MAP: dict[str, str] = {
    # Question ID based
    "SF-01": "Sleep",
    "SE-01": "Social_Support_Checkin",
    "GW-01": "Self_Reported_Wellbeing",
    # Structured output key based
    "sleep_score": "Sleep",
    "perceived_support_score": "Social_Support_Checkin",
    "wellbeing_score": "Self_Reported_Wellbeing",
}


def _extract_from_current_state(current_state: dict[str, Any]) -> dict[str, Any]:
    """Extract known fields from patient_context['current_state']."""
    extracted: dict[str, Any] = {}
    if not isinstance(current_state, dict):
        return extracted

    for field in REQUIRED_STRUCTURED_RISK_FIELDS:
        if field in current_state:
            val = current_state[field]
            extracted[field] = val if val is not None else None

    # Handle lowercase/alternate aliases if present
    alias_map = {
        "mood": "Mood",
        "stress": "Stress",
        "sleep": "Sleep",
        "functioning": "Functioning",
        "safety": "Safety",
        "social_support_checkin": "Social_Support_Checkin",
        "social_support": "Social_Support_Checkin",
        "self_reported_wellbeing": "Self_Reported_Wellbeing",
        "wellbeing": "Self_Reported_Wellbeing",
    }
    for alias, target in alias_map.items():
        if target not in extracted or extracted[target] is None:
            if alias in current_state and current_state[alias] is not None:
                extracted[target] = current_state[alias]

    return extracted


def _extract_from_interaction_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract answers from a list of interaction records."""
    extracted: dict[str, Any] = {}
    if not isinstance(records, list):
        return extracted

    for rec in records:
        if not isinstance(rec, dict):
            continue
        if not rec.get("answered", False) or rec.get("skipped", False):
            continue

        q_id = rec.get("question_id")
        structured_out = rec.get("structured_output")

        # Extract by question ID
        if q_id == "SF-01":
            if isinstance(structured_out, dict) and "sleep_score" in structured_out:
                extracted["Sleep"] = structured_out["sleep_score"]
            elif rec.get("answer") is not None:
                try:
                    extracted["Sleep"] = int(rec["answer"])
                except (ValueError, TypeError):
                    pass

        elif q_id == "SE-01":
            if isinstance(structured_out, dict) and "perceived_support_score" in structured_out:
                extracted["Social_Support_Checkin"] = structured_out["perceived_support_score"]
            elif rec.get("answer") is not None:
                try:
                    extracted["Social_Support_Checkin"] = int(rec["answer"])
                except (ValueError, TypeError):
                    pass

        elif q_id == "GW-01":
            if isinstance(structured_out, dict) and "wellbeing_score" in structured_out:
                extracted["Self_Reported_Wellbeing"] = structured_out["wellbeing_score"]
                # GW-01 also captures baseline mood
                if "Mood" not in extracted:
                    extracted["Mood"] = structured_out["wellbeing_score"]
            elif rec.get("answer") is not None:
                try:
                    score = int(rec["answer"])
                    extracted["Self_Reported_Wellbeing"] = score
                    if "Mood" not in extracted:
                        extracted["Mood"] = score
                except (ValueError, TypeError):
                    pass

        elif q_id == "SF-02":
            if isinstance(structured_out, dict) and "functioning_level" in structured_out:
                extracted["Functioning"] = structured_out["functioning_level"]

        elif q_id == "SA-01":
            if isinstance(structured_out, dict) and "feels_safe" in structured_out:
                extracted["Safety"] = structured_out["feels_safe"]

        elif q_id in ("ES-02", "ES-06"):
            if isinstance(structured_out, dict):
                score = structured_out.get("event_coping_score") or structured_out.get("hypervigilance_score")
                if score is not None:
                    extracted["Stress"] = score

        # Check structured_output keys directly
        if isinstance(structured_out, dict):
            for k, target in _QUESTION_ANSWER_FIELD_MAP.items():
                if k in structured_out and structured_out[k] is not None:
                    extracted[target] = structured_out[k]

    return extracted


def extract_structured_risk_payload(
    source: dict[str, Any] | list[dict[str, Any]] | None = None,
    *,
    patient_context: dict[str, Any] | None = None,
    history_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Produce the exact 7-field Structured Risk Engine payload.

    Parameters
    ----------
    source : dict | list | None, optional
        A patient_context dict, a MedhaState dict, a current_state dict,
        or a list of interaction records.
    patient_context : dict | None, optional
        Explicit patient context dict (e.g. from load_patient_context).
    history_records : list | None, optional
        Interaction records from the current session or check-in history.

    Returns
    -------
    dict[str, Any]
        Dictionary with exactly the 7 keys:
        {
            "Mood": <value | None>,
            "Stress": <value | None>,
            "Sleep": <value | None>,
            "Functioning": <value | None>,
            "Safety": <value | None>,
            "Social_Support_Checkin": <value | None>,
            "Self_Reported_Wellbeing": <value | None>
        }
    """
    accumulated: dict[str, Any] = {}

    # 1. Inspect 'source' if provided
    if isinstance(source, list):
        accumulated.update(_extract_from_interaction_records(source))
    elif isinstance(source, dict):
        if "patient_context" in source and isinstance(source["patient_context"], dict):
            p_ctx = source["patient_context"]
            curr = p_ctx.get("current_state", {})
            accumulated.update(_extract_from_current_state(curr))
        elif "current_state" in source and isinstance(source["current_state"], dict):
            accumulated.update(_extract_from_current_state(source["current_state"]))
        else:
            accumulated.update(_extract_from_current_state(source))

    # 2. Inspect explicit 'patient_context' if provided
    if isinstance(patient_context, dict):
        curr = patient_context.get("current_state", {})
        accumulated.update(_extract_from_current_state(curr))

    # 3. Inspect explicit 'history_records' (takes precedence as live session updates)
    if isinstance(history_records, list):
        session_answers = _extract_from_interaction_records(history_records)
        accumulated.update(session_answers)

    # 4. Build exact 7-field contract dictionary
    payload: dict[str, Any] = {}
    for field in REQUIRED_STRUCTURED_RISK_FIELDS:
        val = accumulated.get(field)
        payload[field] = val if val is not None else None

    return payload


def structured_risk_payload_to_state(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Wrap a Structured Risk payload for storage in MedhaState.

    The payload is stored informatively inside::
        patient_context["structured_risk_payload"]

    Following the same pattern as behaviour_payload_to_state() and
    speech_signals_to_state().
    """
    if not isinstance(payload, dict) or not payload:
        return {}

    # Ensure all 7 fields are present
    normalized = {
        field: payload.get(field, None)
        for field in REQUIRED_STRUCTURED_RISK_FIELDS
    }

    return {
        "patient_context": {
            "structured_risk_payload": normalized
        }
    }
