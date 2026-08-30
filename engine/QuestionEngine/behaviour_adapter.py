"""
behaviour_adapter.py
====================
QE → Behaviour Engine raw-input adapter (Option A).

PURPOSE
-------
Convert existing Question Engine session and question-interaction data into
the raw Behaviour payload that the Behaviour Engine expects as input.

This adapter:
  - Produces a single, self-contained dict per session (the "Behaviour payload").
  - Does NOT calculate any Behaviour features (completion rate, skip rate,
    session duration, baseline z-scores, inactivity score, anomaly score,
    behavioural trends, etc.).  Those are the Behaviour Engine's responsibility.
  - Does NOT read from the Excel dataset.
  - Does NOT modify any existing QE behaviour.

OPTION A ASSUMPTIONS
--------------------
One expected check-in per day.
enrollment_date is the only additional information needed (beyond the QE session
data) to determine expected check-ins.  It is supplied by the caller — never
read from the dataset and never hardcoded here.

BEHAVIOUR PAYLOAD SCHEMA
------------------------
Session envelope::

    {
        "patient_id":          str | None,
        "enrollment_date":     str | None,   # ISO-8601 date, caller-supplied
        "session_id":          str | None,
        "session_start_time":  str | None,   # ISO-8601 datetime
        "session_end_time":    str | None,   # ISO-8601 datetime
        "session_status":      str | None,   # "completed" | "abandoned" | …
        "questions_presented": int,
        "questions_answered":  int,
        "questions":           list[dict]    # per-question sub-records
    }

Per-question sub-record::

    {
        "question_id":             str,
        "question_order":          int | None,
        "question_presented_time": str | None,   # ISO-8601 datetime
        "answer_submitted_time":   str | None,   # ISO-8601 datetime
        "answered":                bool,
        "skipped":                 bool,
        "response_text_length":    int | None,   # char count for text; None for structured
        "modality":                str | None
    }

response_text_length rules
--------------------------
- optional_text or optional_text_or_voice with a non-empty string answer →
      len(answer)   (character count)
- optional_text or optional_text_or_voice with no answer (skipped) →
      None
- Any structured response type (scale_1_5, yes_no, multiple_choice, …) →
      None   (not 0)
- response_type absent from record →
      None

USAGE
-----
    from behaviour_adapter import (
        session_to_behaviour_payload,
        behaviour_payload_to_state,
    )
    from medha_state import MedhaState

    payload = session_to_behaviour_payload(
        session=session_record,
        history_records=records_for_session,
        enrollment_date="2026-01-15",    # caller supplies this
    )

    # Store informatively in MedhaState (no QE trigger is activated).
    state = MedhaState(scheduled_checkin_due=True)
    state.update(behaviour_payload_to_state(payload))

ADAPTER CONTRACT
----------------
This module MUST:
  - Return plain dicts safe to pass to MedhaState.update().
  - Handle missing optional fields gracefully (None, not KeyError).
  - Preserve all timestamps and enrollment_date verbatim.

This module MUST NOT:
  - Calculate any Behaviour Engine feature.
  - Activate any QE trigger flag.
  - Read from disk (Excel, JSON files) itself.
  - Invent patient IDs when none are present in the inputs.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

# Response types that carry free-text content eligible for response_text_length.
_TEXT_RESPONSE_TYPES: frozenset = frozenset({
    "optional_text",
    "optional_text_or_voice",
})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _compute_response_text_length(interaction: dict) -> int | None:
    """
    Return the character count of a text answer, or None.

    Rules
    -----
    - Only optional_text and optional_text_or_voice responses carry text.
    - For those types, return len(answer) when a non-empty string is present.
    - For all structured types (scale_1_5, yes_no, multiple_choice, …) or
      when response_type is absent: return None (never 0).
    - Skipped / unanswered text questions also return None.

    Parameters
    ----------
    interaction : dict
        One interaction record from history.json (or equivalent in-memory form).

    Returns
    -------
    int | None
    """
    response_type = interaction.get("response_type")

    if response_type not in _TEXT_RESPONSE_TYPES:
        return None

    answer = interaction.get("answer")

    if not isinstance(answer, str) or not answer:
        return None

    return len(answer)


def _build_question_record(interaction: dict) -> dict:
    """
    Convert one QE interaction record into a Behaviour per-question sub-record.

    Missing optional fields are preserved as None — no KeyError, no invention.

    Parameters
    ----------
    interaction : dict
        One interaction record from history.json (or equivalent in-memory form).

    Returns
    -------
    dict
        Per-question sub-record conforming to the Behaviour payload schema.
    """
    return {
        "question_id":             interaction.get("question_id"),
        "question_order":          interaction.get("question_order"),
        "question_presented_time": interaction.get("question_presented_time"),
        "answer_submitted_time":   interaction.get("answer_submitted_time"),
        "answered":                bool(interaction.get("answered", False)),
        "skipped":                 bool(interaction.get("skipped", False)),
        "response_text_length":    _compute_response_text_length(interaction),
        "modality":                interaction.get("modality"),
    }


def _resolve_patient_id(
    session: dict,
    history_records: list[dict],
    explicit_patient_id: str | None,
) -> str | None:
    """
    Normalise patient_id from heterogeneous sources.

    Priority
    --------
    1. explicit_patient_id argument (caller-supplied)
    2. patient_id from the first history record (history.json field name)
    3. user_id from the session record (sessions.json field name)
    4. None  — never invent an ID

    Parameters
    ----------
    session          : dict   Session record (may use "user_id").
    history_records  : list   Interaction records (may use "patient_id").
    explicit_patient_id : str | None  Caller override.

    Returns
    -------
    str | None
    """
    if explicit_patient_id is not None:
        return explicit_patient_id

    if history_records:
        pid = history_records[0].get("patient_id")
        if pid is not None:
            return pid

    return session.get("user_id")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def session_to_behaviour_payload(
    session: dict,
    history_records: list[dict],
    enrollment_date: str | None,
    patient_id: str | None = None,
) -> dict:
    """
    Convert QE session + interaction data into a Behaviour Engine raw payload.

    This function performs data extraction and field normalisation only.
    It does NOT compute any Behaviour feature.

    Parameters
    ----------
    session : dict
        One session record, e.g. from sessions.json::

            {
                "user_id":             "V0001",
                "session_id":          "abc-123",
                "session_start_time":  "2026-08-28T21:37:36",
                "session_end_time":    "2026-08-28T21:37:36",
                "session_status":      "completed",
                "questions_presented": 2,
                "questions_answered":  1
            }

        The field "user_id" is normalised to "patient_id" in the output.

    history_records : list[dict]
        All interaction records that belong to this session, in the order they
        were recorded.  Each record is one dict from history.json (or the
        equivalent in-memory list).  May be an empty list.

        Older records that pre-date session_demo.py will be missing
        session_id, question_order, question_presented_time,
        answer_submitted_time, and modality.  Those fields default to None.

    enrollment_date : str | None
        ISO-8601 date string supplied by the caller (e.g. "2026-01-15").
        Option A assumes one expected check-in per day; the Behaviour Engine
        uses enrollment_date to compute how many check-ins were expected.
        This adapter preserves the value verbatim — it does not validate it.
        Must NOT be read from the dataset or hardcoded.

    patient_id : str | None, optional
        Explicit patient_id override.  When supplied, takes priority over any
        patient_id found in history_records or user_id in session.
        Defaults to None (fall-through to history / session sources).

    Returns
    -------
    dict
        Behaviour Engine raw payload conforming to the schema described in the
        module docstring.  All fields are always present; optional ones are
        None rather than absent.

    Examples
    --------
    Minimal completed session::

        session = {
            "user_id": "P001",
            "session_id": "s-001",
            "session_start_time": "2026-08-28T09:00:00",
            "session_end_time":   "2026-08-28T09:05:00",
            "session_status":     "completed",
            "questions_presented": 1,
            "questions_answered":  1,
        }
        records = [
            {
                "patient_id":   "P001",
                "question_id":  "GW-01",
                "answered":     True,
                "skipped":      False,
                "response_type": "scale_1_5",
                "answer":       "4",
            }
        ]
        payload = session_to_behaviour_payload(session, records, "2026-01-15")
    """
    if not isinstance(session, dict):
        session = {}

    if not isinstance(history_records, list):
        history_records = []

    resolved_patient_id = _resolve_patient_id(session, history_records, patient_id)

    questions = [_build_question_record(rec) for rec in history_records]

    return {
        "patient_id":          resolved_patient_id,
        "enrollment_date":     enrollment_date,
        "session_id":          session.get("session_id"),
        "session_start_time":  session.get("session_start_time"),
        "session_end_time":    session.get("session_end_time"),
        "session_status":      session.get("session_status"),
        "questions_presented": int(session.get("questions_presented", 0)),
        "questions_answered":  int(session.get("questions_answered", 0)),
        "questions":           questions,
    }


def behaviour_payload_to_state(payload: Any) -> dict:
    """
    Wrap a Behaviour raw payload for storage in MedhaState.

    The payload is stored informatively inside::

        patient_context["behaviour_payload"]

    This follows the same pattern as nlp_signals_to_state() and
    speech_signals_to_state() in model_adapters.py.

    NO QE trigger flag is activated by this function.  The Behaviour Engine
    is responsible for computing features and signals from the raw payload;
    those signals would be delivered back to the QE via the existing
    behaviour_signals_to_state() adapter in model_adapters.py.

    Parameters
    ----------
    payload : dict
        Return value of session_to_behaviour_payload().
        Non-dict values are treated as empty and return {}.

    Returns
    -------
    dict
        Partial MEDHA State dict::

            {
                "patient_context": {
                    "behaviour_payload": { ... }
                }
            }

        Safe to pass to MedhaState.update().
        Does NOT contain any QE trigger flag keys.

    Example
    -------
        payload = session_to_behaviour_payload(session, records, enrollment_date)
        state = MedhaState(scheduled_checkin_due=True)
        state.update(behaviour_payload_to_state(payload))
        # → state._patient_context["behaviour_payload"] = payload
        # → No QE trigger is activated.
    """
    if not isinstance(payload, dict) or not payload:
        return {}

    return {
        "patient_context": {
            "behaviour_payload": payload
        }
    }
