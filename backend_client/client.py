"""
MEDHA Backend HTTP Client
==========================

Thin synchronous wrapper around the MEDHA FastAPI backend REST API.

Design principles:
  - One class, one responsibility: HTTP → typed Python objects.
  - All auth is passed as Bearer JWT. The client stores no state between calls
    except the base URL (which is immutable after construction).
  - Missing fields (e.g., behaviour_data=None) are stripped from JSON payloads
    rather than sending explicit nulls, so the backend never sees unexpected keys.
  - All HTTP errors are converted to typed MedhaClientError subclasses so callers
    never have to inspect raw status codes.
  - Connection failures are caught and re-raised as MedhaConnectionError.
  - No retry logic in this layer — the Streamlit app handles user-facing retries
    via st.error() and the user clicking again.

Backend URL:
  Reads from environment variable MEDHA_BACKEND_URL.
  Defaults to http://localhost:8000 (both servers running locally for MVP).

Usage:
  client = MedhaBackendClient()
  token = client.login("user@example.com", "Password123!")
  session = client.create_session(token)
  result = client.send_message(token, session["id"], "Hello")
  client.end_session(token, session["id"])
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from backend_client.exceptions import (
    MedhaAuthError,
    MedhaClientError,
    MedhaConnectionError,
    MedhaConflictError,
    MedhaForbiddenError,
    MedhaNotFoundError,
    MedhaServerError,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_BACKEND_URL = "http://localhost:8000"
_API_PREFIX = "/api/v1"
_DEFAULT_TIMEOUT = 30.0  # seconds


# ---------------------------------------------------------------------------
# Response dataclasses (avoid coupling to backend Pydantic models)
# ---------------------------------------------------------------------------

@dataclass
class LoginResult:
    """Result of a successful login."""
    access_token: str
    token_type: str
    user_id: str
    role: str
    name: str
    email: str


@dataclass
class SessionResult:
    """Minimal session record from the backend."""
    id: str                    # UUID string
    session_identifier: str
    case_id: str
    victim_id: str
    timepoint: int
    status: str


@dataclass
class ChatTurnResult:
    """Single chat turn result from the backend."""
    session_id: str
    turn_index: int
    user_message: str
    assistant_response: str
    safety_triggered: bool
    timestamp: Optional[str] = None


@dataclass
class ChatMessage:
    """Single message from history endpoint."""
    id: str
    role: str
    content: str
    timestamp: Optional[str] = None


@dataclass
class EventSubmitResult:
    """Result of a batch event submission."""
    submitted: int
    duplicates_ignored: int


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class MedhaBackendClient:
    """
    Synchronous HTTP client for the MEDHA FastAPI backend.

    All methods raise typed MedhaClientError subclasses on failure.
    All methods accept a `token` parameter (Bearer JWT) as the first positional
    argument after `self` so callers always know where auth lives.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = _DEFAULT_TIMEOUT):
        """
        Parameters
        ----------
        base_url:
            Backend URL. Reads MEDHA_BACKEND_URL env var if not provided.
            Defaults to http://localhost:8000.
        timeout:
            Request timeout in seconds.
        """
        self._base_url = (
            base_url
            or os.environ.get("MEDHA_BACKEND_URL", _DEFAULT_BACKEND_URL)
        ).rstrip("/")
        self._timeout = timeout

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Constructs a full URL from a relative API path."""
        return f"{self._base_url}{_API_PREFIX}{path}"

    @staticmethod
    def _auth_headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _raise_for_status(self, response: httpx.Response) -> None:
        """
        Converts HTTP error responses into typed MedhaClientError exceptions.
        Extracts the 'detail' field from the backend JSON body where available.
        """
        if response.is_success:
            return

        # Try to extract a human-readable error message from the body
        try:
            body = response.json()
            detail = body.get("detail", response.text)
        except Exception:
            detail = response.text or f"HTTP {response.status_code}"

        code = response.status_code

        if code == 401:
            raise MedhaAuthError(str(detail), status_code=code)
        if code == 403:
            raise MedhaForbiddenError(str(detail), status_code=code)
        if code == 404:
            raise MedhaNotFoundError(str(detail), status_code=code)
        if code == 409:
            raise MedhaConflictError(str(detail), status_code=code)
        if code >= 500:
            raise MedhaServerError(str(detail), status_code=code)

        # Any other 4xx
        raise MedhaClientError(str(detail), status_code=code)

    def _get(self, token: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = httpx.get(
                self._url(path),
                headers=self._auth_headers(token),
                timeout=self._timeout,
                **kwargs,
            )
        except httpx.ConnectError as e:
            raise MedhaConnectionError(
                f"Cannot reach MEDHA backend at {self._base_url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise MedhaConnectionError(f"Request timed out: {e}") from e
        self._raise_for_status(resp)
        return resp

    def _post(self, token: Optional[str], path: str, **kwargs: Any) -> httpx.Response:
        headers = self._auth_headers(token) if token else {}
        try:
            resp = httpx.post(
                self._url(path),
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            )
        except httpx.ConnectError as e:
            raise MedhaConnectionError(
                f"Cannot reach MEDHA backend at {self._base_url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise MedhaConnectionError(f"Request timed out: {e}") from e
        self._raise_for_status(resp)
        return resp

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def login(self, email: str, password: str) -> LoginResult:
        """
        Authenticates with the MEDHA backend.

        Parameters
        ----------
        email:
            User email address.
        password:
            User password.

        Returns
        -------
        LoginResult
            Contains access_token plus basic user metadata.

        Raises
        ------
        MedhaAuthError
            If credentials are invalid or account is suspended.
        MedhaConnectionError
            If the backend is unreachable.
        """
        resp = self._post(
            token=None,
            path="/auth/login",
            json={"email": email, "password": password},
        )
        data = resp.json()
        # Backend TokenResponse: {access_token, token_type, expires_in, user: {id, role, name, email, ...}}
        user = data.get("user", {})
        return LoginResult(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            user_id=str(user.get("id", "")),
            role=str(user.get("role", "")),
            name=user.get("name", ""),
            email=user.get("email", email),
        )


    def create_session(
        self,
        token: str,
        case_id: Optional[str] = None,
        session_identifier: Optional[str] = None,
    ) -> SessionResult:
        """
        Creates a new conversation session in the backend.

        Parameters
        ----------
        token:
            Bearer JWT from login().
        case_id:
            Required if the caller is a THERAPIST.
            For USER role, the backend resolves the active case automatically.
        session_identifier:
            Optional human-readable identifier for the session.

        Returns
        -------
        SessionResult

        Raises
        ------
        MedhaAuthError, MedhaForbiddenError, MedhaNotFoundError, MedhaConnectionError
        """
        payload: Dict[str, Any] = {}
        if case_id:
            payload["case_id"] = case_id
        if session_identifier:
            payload["session_identifier"] = session_identifier

        resp = self._post(token=token, path="/sessions", json=payload)
        data = resp.json()
        return SessionResult(
            id=str(data["id"]),
            session_identifier=data["session_identifier"],
            case_id=str(data["case_id"]),
            victim_id=data.get("victim_id", ""),
            timepoint=data.get("timepoint", 1),
            status=data.get("status", "ACTIVE"),
        )

    def end_session(self, token: str, session_id: str) -> None:
        """
        Ends an active session.

        Parameters
        ----------
        token:
            Bearer JWT.
        session_id:
            UUID string of the session to end.

        Raises
        ------
        MedhaAuthError, MedhaForbiddenError, MedhaNotFoundError, MedhaConnectionError
        """
        self._post(token=token, path=f"/sessions/{session_id}/end", json={})

    def send_message(
        self,
        token: str,
        session_id: str,
        message: str,
        behaviour_data: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatTurnResult:
        """
        Sends a user message through the MEDHA pipeline and returns the response.

        Parameters
        ----------
        token:
            Bearer JWT.
        session_id:
            UUID string of the active session.
        message:
            User text content.
        behaviour_data:
            Optional dict of behaviour feature values. Passed to the behaviour
            adapter in the ConversationManager. Allowed keys match BEHAVIOUR_FEATURES.
        language:
            Optional language hint ('en', 'hi', 'hinglish').
        metadata:
            Optional per-turn metadata (e.g., voice_features).

        Returns
        -------
        ChatTurnResult

        Raises
        ------
        MedhaAuthError, MedhaForbiddenError, MedhaServerError, MedhaConnectionError
        """
        payload: Dict[str, Any] = {"message": message}
        if behaviour_data:
            payload["behaviour_data"] = behaviour_data
        if language:
            payload["language"] = language
        if metadata:
            payload["metadata"] = metadata

        resp = self._post(token=token, path=f"/chat/sessions/{session_id}/message", json=payload)
        data = resp.json()
        return ChatTurnResult(
            session_id=data.get("session_id", session_id),
            turn_index=data.get("turn_index", 0),
            user_message=data.get("user_message", message),
            assistant_response=data.get("assistant_response", ""),
            safety_triggered=data.get("safety_triggered", False),
            timestamp=data.get("timestamp"),
        )

    def get_history(self, token: str, session_id: str) -> List[ChatMessage]:
        """
        Retrieves ordered message history for a session.

        Parameters
        ----------
        token:
            Bearer JWT.
        session_id:
            UUID string of the session.

        Returns
        -------
        List[ChatMessage]
            Messages in chronological order.
        """
        resp = self._get(token=token, path=f"/chat/sessions/{session_id}/history")
        data = resp.json()
        messages = data.get("messages", [])
        return [
            ChatMessage(
                id=str(m.get("id", "")),
                role=m.get("role", ""),
                content=m.get("content", ""),
                timestamp=m.get("timestamp"),
            )
            for m in messages
        ]

    def submit_events(
        self,
        token: str,
        events: List[Dict[str, Any]],
    ) -> EventSubmitResult:
        """
        Submits a batch of raw behaviour events to the backend.
        Events are processed idempotently (duplicate event_ids are silently ignored).

        Parameters
        ----------
        token:
            Bearer JWT.
        events:
            List of event dicts. Each must have at minimum:
            {
              "event_id": str (UUID),
              "event_type": str,
              "occurred_at": str (ISO-8601),
              "metadata": dict (optional)
            }
            session_id and case_id are resolved server-side from the authenticated user's
            active session / case.

        Returns
        -------
        EventSubmitResult
        """
        resp = self._post(token=token, path="/events/batch", json={"events": events})
        data = resp.json()
        return EventSubmitResult(
            submitted=data.get("submitted", len(events)),
            duplicates_ignored=data.get("duplicates_ignored", 0),
        )
