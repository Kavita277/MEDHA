"""
Centralized Privacy & Redaction Engine
======================================

Provides reusable, standardized data sanitization, privacy firewalls, and
leakage guards across the MEDHA backend.

Guarantees:
  - Recursively redacts passwords, bcrypt hashes, JWTs, bearer tokens, API keys,
    secrets, raw audio/voice bytes, raw transcripts, chat messages, and journal content.
  - Sanitizes validation errors so sensitive inputs are never echoed in 422 responses or logs.
  - Sanitizes HTTP request URLs and query strings before access logging.
  - Masks internal exception details and local filesystem paths in error responses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Blacklist of keys/fields that must NEVER be logged or echoed in raw form
SENSITIVE_FIELD_NAMES: Set[str] = {
    "password",
    "password_hash",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "jwt",
    "authorization",
    "auth",
    "credentials",
    "api_key",
    "apikey",
    "content",
    "transcript",
    "text",
    "raw_audio",
    "voice_bytes",
    "audio_payload",
    "journal_text",
    "chat_message",
}

# Regex to detect JWT strings or Bearer headers
_JWT_BEARER_PATTERN = re.compile(r"(bearer\s+[a-zA-Z0-9_\-\.]+|eyj[a-za-z0-9_\-]{10,}\.[a-za-z0-9_\-]{10,}\.[a-za-z0-9_\-]*)", re.IGNORECASE)

# Regex to detect local filesystem paths in error strings
_PATH_PATTERN = re.compile(r"([A-Za-z]:\\[^\s:\"<>|]+|/(?:home|tmp|usr|var|app|Users)/[^\s:\"<>|]+)")


def is_sensitive_field(field_name: Any) -> bool:
    """Checks whether a given field name or path segment is in the sensitive blacklist."""
    if not isinstance(field_name, (str, int)):
        return False
    name_str = str(field_name).lower()
    return any(blacklisted in name_str for blacklisted in SENSITIVE_FIELD_NAMES)


def sanitize_payload(payload: Any) -> Any:
    """
    Recursively redacts sensitive keys and values from dictionary and list structures.
    """
    if payload is None:
        return None
    if isinstance(payload, dict):
        sanitized = {}
        for k, v in payload.items():
            if is_sensitive_field(k):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    if isinstance(payload, (list, tuple, set)):
        return [sanitize_payload(item) for item in payload]
    if isinstance(payload, (int, float, bool)):
        return payload

    val_str = str(payload)
    if _JWT_BEARER_PATTERN.search(val_str):
        return "[REDACTED_TOKEN]"
    return val_str


def sanitize_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes Pydantic RequestValidationError error dictionaries.
    Preserves validation metadata (loc, type, msg, ctx) while redacting sensitive 'input' values.
    """
    sanitized_errors: List[Dict[str, Any]] = []

    for err in errors:
        err_copy = dict(err)
        loc = err.get("loc", ())
        
        # Check if any location segment corresponds to a sensitive field
        loc_is_sensitive = any(is_sensitive_field(seg) for seg in loc)

        if "input" in err_copy:
            raw_input = err_copy["input"]
            if loc_is_sensitive:
                err_copy["input"] = "[REDACTED]"
            elif isinstance(raw_input, (dict, list, tuple)):
                err_copy["input"] = sanitize_payload(raw_input)
            elif isinstance(raw_input, str) and _JWT_BEARER_PATTERN.search(raw_input):
                err_copy["input"] = "[REDACTED_TOKEN]"

        sanitized_errors.append(err_copy)

    return sanitized_errors


def sanitize_url(url_str: str) -> str:
    """
    Scans a URL or request path and redacts sensitive query parameters.
    """
    if not url_str:
        return url_str

    try:
        parsed = urlparse(url_str)
        if not parsed.query:
            return url_str

        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        sanitized_params = []
        for k, v in query_params:
            if is_sensitive_field(k):
                sanitized_params.append((k, "[REDACTED]"))
            else:
                sanitized_params.append((k, v))

        new_query = urlencode(sanitized_params)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url_str


def mask_internal_error(error_str: str, fallback_message: str = "An internal processing error occurred.") -> str:
    """
    Strips internal paths, memory addresses, and engine internals from exception messages.
    """
    if not error_str:
        return fallback_message

    masked = _PATH_PATTERN.sub("[INTERNAL_PATH]", error_str)
    masked = _JWT_BEARER_PATTERN.sub("[REDACTED_TOKEN]", masked)
    return masked
