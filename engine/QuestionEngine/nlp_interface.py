"""
nlp_interface.py
================
Model-agnostic NLP adapter for the MEDHA Question Engine.

THE ONLY ENTRY POINT the Question Engine uses for free-text extraction:

    from nlp_interface import extract_free_text_signals
    structured_output = extract_free_text_signals(answer)

Architecture
------------
optional_text / optional_text_or_voice
        ↓
extract_free_text_signals(text)
        ↓
  ┌─ medha_nlp present? ──────────────────────────→ structured MEDHA signals
  │
  └─ not present (teammate model not yet here) ───→ extraction-unavailable sentinel
                 OR call raises                  ───→ extraction-failed sentinel
                 (session continues, no crash)

Gemini / llm_extractor is NOT called here and is NOT a fallback.

Where the teammate connects
---------------------------
Create a file called ``medha_nlp.py`` (or a package ``medha_nlp/``) in the
same repository directory, exporting exactly:

    def extract_free_text_signals(text: str) -> dict:
        ...

The output must match MEDHA_EXTRACTION_SCHEMA below.
No other changes to the Question Engine are required.

Constraints the teammate NLP model must respect
-----------------------------------------------
- Extract ONLY information explicitly present in the user's text.
- Do NOT diagnose, infer clinical conditions, assign risk/severity scores.
- Do NOT decide which question should be asked or what action to take.
- Return null / [] when information is not clearly present.
- safety_concern_mentioned may be True when the user explicitly states a
  physical safety concern — but the model must NOT determine danger level
  or emergency action.
"""

# ---------------------------------------------------------------------------
# Agreed extraction schema (for documentation and validation)
# ---------------------------------------------------------------------------

MEDHA_EXTRACTION_SCHEMA = {
    "mentioned_emotions":       list,   # list[str]   – emotions explicitly stated
    "mentioned_problems":       list,   # list[str]   – problems explicitly stated
    "linked_case_event":        (str, type(None)),  # str | None
    "sleep_issue":              (bool, type(None)),  # bool | None
    "social_support_issue":     (bool, type(None)),  # bool | None
    "safety_concern_mentioned": (bool, type(None)),  # bool | None
    "needs_human_followup":     (bool, type(None)),  # bool | None
    "confidence":               (int, float),        # 0.0–1.0
}

MEDHA_SCHEMA_REQUIRED_FIELDS = frozenset(MEDHA_EXTRACTION_SCHEMA.keys())


def _empty_extraction():
    """Return the canonical zero-signal extraction result."""
    return {
        "mentioned_emotions":       [],
        "mentioned_problems":       [],
        "linked_case_event":        None,
        "sleep_issue":              None,
        "social_support_issue":     None,
        "safety_concern_mentioned": None,
        "needs_human_followup":     None,
        "confidence":               0.0,
    }


def _unavailable_sentinel(raw_text: str) -> dict:
    """
    Returned when the NLP model module is not present in this repository.
    The session continues; structured fields are empty but clearly labelled.
    """
    result = _empty_extraction()
    result["extraction_status"] = "unavailable"
    result["extraction_note"] = (
        "NLP model not connected. "
        "Deliver medha_nlp.py to activate free-text extraction. "
        "Raw text preserved."
    )
    result["raw_text"] = raw_text
    return result


def _failed_sentinel(raw_text: str, error: str) -> dict:
    """
    Returned when the NLP model is present but raises an exception.
    The session continues; the error is recorded for diagnostics.
    """
    result = _empty_extraction()
    result["extraction_status"] = "failed"
    result["extraction_error"] = error
    result["raw_text"] = raw_text
    return result


# ---------------------------------------------------------------------------
# Validation helper (available to the teammate's NLP model for self-check)
# ---------------------------------------------------------------------------

def validate_extracted_signals(data: dict) -> tuple:
    """
    Validate the semantic shape of a MEDHA extraction output dict.

    Returns (True, None)          when the dict is valid.
    Returns (False, error_message) when it is invalid.

    This is the same validation logic that was previously in llm_extractor.py,
    now exposed here so any NLP implementation can use it without importing
    Gemini-related code.
    """
    missing = MEDHA_SCHEMA_REQUIRED_FIELDS - set(data.keys())
    if missing:
        return False, f"Missing fields: {sorted(missing)}"

    if not isinstance(data["mentioned_emotions"], list):
        return False, "mentioned_emotions must be a list"

    if not isinstance(data["mentioned_problems"], list):
        return False, "mentioned_problems must be a list"

    if (
        data["linked_case_event"] is not None
        and not isinstance(data["linked_case_event"], str)
    ):
        return False, "linked_case_event must be string or null"

    boolean_fields = [
        "sleep_issue",
        "social_support_issue",
        "safety_concern_mentioned",
        "needs_human_followup",
    ]
    for field in boolean_fields:
        value = data[field]
        if value is not None and not isinstance(value, bool):
            return False, f"{field} must be boolean or null"

    confidence = data["confidence"]
    if not isinstance(confidence, (int, float)):
        return False, "confidence must be a number"
    if not 0 <= confidence <= 1:
        return False, "confidence must be between 0 and 1"

    return True, None


# ---------------------------------------------------------------------------
# Public interface — the ONE function the Question Engine calls
# ---------------------------------------------------------------------------

def extract_free_text_signals(text: str) -> dict:
    """
    Extract structured MEDHA signals from a free-text user response.

    Parameters
    ----------
    text : str
        The user's free-text answer to an optional_text or
        optional_text_or_voice question.

    Returns
    -------
    dict
        A dict matching MEDHA_EXTRACTION_SCHEMA, always present and safe.
        Additional diagnostic keys (extraction_status, extraction_note,
        extraction_error, raw_text) are included when extraction could not
        be performed.

    Notes
    -----
    - If medha_nlp is not installed: returns extraction-unavailable sentinel.
    - If medha_nlp raises:           returns extraction-failed sentinel.
    - Gemini / llm_extractor is NOT called under any circumstances.
    - The Question Engine session never crashes due to NLP unavailability.
    """
    try:
        import medha_nlp  # teammate's real NLP model — not yet in this repo
    except ImportError:
        # Teammate model not yet present — return safe unavailable sentinel.
        return _unavailable_sentinel(text)

    try:
        result = medha_nlp.extract_free_text_signals(text)

        # Validate the output shape before accepting it.
        valid, error = validate_extracted_signals(result)
        if not valid:
            return _failed_sentinel(
                text,
                f"NLP model returned invalid schema: {error}"
            )

        return result

    except Exception as exc:  # noqa: BLE001
        return _failed_sentinel(text, str(exc))
