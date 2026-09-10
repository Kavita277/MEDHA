"""
Backend Client Unit Tests
==========================

Tests for MedhaBackendClient using unittest.mock to patch httpx calls.
No real HTTP connections are made; all responses are synthetic.

Coverage:
  A. login() returns LoginResult on HTTP 200
  B. login() raises MedhaAuthError on HTTP 401
  C. login() raises MedhaConnectionError when backend unreachable
  D. login() raises MedhaForbiddenError on HTTP 403 (suspended account)
  E. create_session() returns SessionResult on HTTP 201
  F. create_session() raises MedhaForbiddenError on HTTP 403
  G. end_session() does not raise on HTTP 200
  H. send_message() returns ChatTurnResult on HTTP 200
  I. send_message() raises MedhaServerError on HTTP 500
  J. get_history() returns ordered ChatMessage list
  K. submit_events() returns EventSubmitResult on HTTP 201
  L. submit_events() silently succeeds when backend returns 201
  M. BackendEventEmitter.emit_turn() calls submit_events once per turn
  N. BackendEventEmitter.emit_session_end() calls submit_events
  O. BackendEventEmitter swallows errors silently (silent=True default)
  P. _deterministic_uuid produces stable, idempotent results
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from backend_client.client import MedhaBackendClient
from backend_client.event_emitter import BackendEventEmitter, _deterministic_uuid, _MEDHA_EVENTS_NS
from backend_client.exceptions import (
    MedhaAuthError,
    MedhaClientError,
    MedhaConnectionError,
    MedhaForbiddenError,
    MedhaServerError,
)

import httpx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, json_body: dict) -> MagicMock:
    """Creates a mock httpx.Response with the given status and JSON body."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.is_success = 200 <= status_code < 300
    mock_resp.json.return_value = json_body
    mock_resp.text = str(json_body)
    return mock_resp


_LOGIN_OK_BODY = {
    "access_token": "test_token_abc",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "role": "USER",
        "name": "Test Patient",
        "email": "patient@test.com",
        "status": "ACTIVE",
    },
}

_SESSION_OK_BODY = {
    "id": "ssssssss-1111-2222-3333-444444444444",
    "session_identifier": "sess_abc123",
    "case_id": "cccccccc-dddd-eeee-ffff-000000000000",
    "victim_id": "V-001",
    "timepoint": 1,
    "status": "ACTIVE",
}

_CHAT_OK_BODY = {
    "session_id": "ssssssss-1111-2222-3333-444444444444",
    "turn_index": 1,
    "user_message": "Hello",
    "assistant_response": "Hi there, how can I help?",
    "safety_triggered": False,
    "timestamp": "2026-09-10T12:00:00Z",
}

_HISTORY_OK_BODY = {
    "session_id": "ssssssss-1111-2222-3333-444444444444",
    "messages": [
        {"id": "m1", "role": "user", "content": "Hello", "timestamp": "2026-09-10T12:00:00Z"},
        {"id": "m2", "role": "assistant", "content": "Hi!", "timestamp": "2026-09-10T12:00:01Z"},
    ],
}

_EVENTS_OK_BODY = {
    "submitted": 2,
    "duplicates_ignored": 0,
}


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestLogin:
    def test_a_login_success(self):
        """A. login() returns LoginResult on HTTP 200."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", return_value=_make_response(200, _LOGIN_OK_BODY)):
            result = client.login("patient@test.com", "Password123!")
        assert result.access_token == "test_token_abc"
        assert result.role == "USER"
        assert result.name == "Test Patient"
        assert result.email == "patient@test.com"

    def test_b_login_401_raises_auth_error(self):
        """B. login() raises MedhaAuthError on HTTP 401."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        resp = _make_response(401, {"detail": "Incorrect email or password"})
        with patch("httpx.post", return_value=resp):
            with pytest.raises(MedhaAuthError):
                client.login("bad@test.com", "wrong")

    def test_c_login_connection_error(self):
        """C. login() raises MedhaConnectionError when backend unreachable."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(MedhaConnectionError):
                client.login("p@t.com", "pass")

    def test_d_login_403_suspended_account(self):
        """D. login() raises MedhaForbiddenError on HTTP 403."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        resp = _make_response(403, {"detail": "Account access denied. Account status is SUSPENDED."})
        with patch("httpx.post", return_value=resp):
            with pytest.raises(MedhaForbiddenError):
                client.login("suspended@test.com", "pass")


class TestCreateSession:
    def test_e_create_session_success(self):
        """E. create_session() returns SessionResult on HTTP 201."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", return_value=_make_response(201, _SESSION_OK_BODY)):
            result = client.create_session(token="tok123")
        assert result.session_identifier == "sess_abc123"
        assert result.victim_id == "V-001"
        assert result.timepoint == 1

    def test_f_create_session_403(self):
        """F. create_session() raises MedhaForbiddenError on HTTP 403."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        resp = _make_response(403, {"detail": "No active case found."})
        with patch("httpx.post", return_value=resp):
            with pytest.raises(MedhaForbiddenError):
                client.create_session(token="tok123")


class TestEndSession:
    def test_g_end_session_success(self):
        """G. end_session() does not raise on HTTP 200."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", return_value=_make_response(200, {})):
            client.end_session(token="tok123", session_id="sess-id")  # must not raise


class TestSendMessage:
    def test_h_send_message_success(self):
        """H. send_message() returns ChatTurnResult on HTTP 200."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", return_value=_make_response(200, _CHAT_OK_BODY)):
            result = client.send_message(token="tok", session_id="sess", message="Hello")
        assert result.assistant_response == "Hi there, how can I help?"
        assert result.turn_index == 1
        assert result.safety_triggered is False

    def test_i_send_message_500_raises_server_error(self):
        """I. send_message() raises MedhaServerError on HTTP 500."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        resp = _make_response(500, {"detail": "Internal Server Error"})
        with patch("httpx.post", return_value=resp):
            with pytest.raises(MedhaServerError):
                client.send_message(token="tok", session_id="sess", message="Hi")


class TestGetHistory:
    def test_j_get_history_returns_ordered_messages(self):
        """J. get_history() returns ordered ChatMessage list."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.get", return_value=_make_response(200, _HISTORY_OK_BODY)):
            messages = client.get_history(token="tok", session_id="sess")
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[0].content == "Hello"


class TestSubmitEvents:
    def test_k_submit_events_success(self):
        """K. submit_events() returns EventSubmitResult on HTTP 201."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        events = [
            {"event_id": str(uuid.uuid4()), "event_type": "chat_message_sent", "occurred_at": "2026-09-10T12:00:00Z"},
            {"event_id": str(uuid.uuid4()), "event_type": "session_start", "occurred_at": "2026-09-10T11:59:59Z"},
        ]
        with patch("httpx.post", return_value=_make_response(201, _EVENTS_OK_BODY)):
            result = client.submit_events(token="tok", events=events)
        assert result.submitted == 2
        assert result.duplicates_ignored == 0

    def test_l_submit_events_201(self):
        """L. submit_events() silently succeeds when backend returns 201."""
        client = MedhaBackendClient(base_url="http://localhost:8000")
        with patch("httpx.post", return_value=_make_response(201, {"submitted": 1, "duplicates_ignored": 0})):
            result = client.submit_events(token="tok", events=[{"event_id": "x", "event_type": "screen_view", "occurred_at": "now"}])
        assert result.submitted == 1


class TestEventEmitter:
    def setup_method(self):
        self.client = MagicMock(spec=MedhaBackendClient)
        self.session_id = str(uuid.uuid4())
        self.emitter = BackendEventEmitter(
            client=self.client,
            session_id=self.session_id,
            silent=False,  # Raise errors in tests
        )

    def test_m_emit_turn_calls_submit_events(self):
        """M. BackendEventEmitter.emit_turn() calls submit_events once per turn."""
        self.emitter.emit_turn(token="tok", turn_index=2, session_duration_seconds=30.0)
        self.client.submit_events.assert_called_once()
        events = self.client.submit_events.call_args[1]["events"]
        # Turn 2 → only chat_message_sent (no session_start on turn 2)
        event_types = [e["event_type"] for e in events]
        assert "chat_message_sent" in event_types
        assert "session_start" not in event_types

    def test_m2_emit_turn_first_turn_includes_session_start(self):
        """M2. First turn emits session_start + chat_message_sent."""
        self.emitter.emit_turn(token="tok", turn_index=1)
        events = self.client.submit_events.call_args[1]["events"]
        event_types = [e["event_type"] for e in events]
        assert "session_start" in event_types
        assert "chat_message_sent" in event_types

    def test_n_emit_session_end_calls_submit_events(self):
        """N. BackendEventEmitter.emit_session_end() calls submit_events."""
        self.emitter.emit_session_end(token="tok")
        self.client.submit_events.assert_called_once()
        events = self.client.submit_events.call_args[1]["events"]
        assert events[0]["event_type"] == "session_end"

    def test_o_silent_emitter_swallows_errors(self):
        """O. BackendEventEmitter swallows errors silently when silent=True."""
        self.client.submit_events.side_effect = MedhaClientError("simulated error")
        silent_emitter = BackendEventEmitter(
            client=self.client,
            session_id=self.session_id,
            silent=True,
        )
        # Must not raise
        silent_emitter.emit_turn(token="tok", turn_index=1)
        silent_emitter.emit_session_end(token="tok")


class TestDeterministicUUID:
    def test_p_same_inputs_same_uuid(self):
        """P. _deterministic_uuid produces stable, idempotent results."""
        sid = str(uuid.uuid4())
        uuid1 = _deterministic_uuid(_MEDHA_EVENTS_NS, sid, "1", "chat_message_sent")
        uuid2 = _deterministic_uuid(_MEDHA_EVENTS_NS, sid, "1", "chat_message_sent")
        assert uuid1 == uuid2

    def test_p2_different_inputs_different_uuid(self):
        """P2. Different inputs produce different UUIDs."""
        sid = str(uuid.uuid4())
        uuid1 = _deterministic_uuid(_MEDHA_EVENTS_NS, sid, "1", "chat_message_sent")
        uuid2 = _deterministic_uuid(_MEDHA_EVENTS_NS, sid, "2", "chat_message_sent")
        assert uuid1 != uuid2

    def test_p3_valid_uuid_format(self):
        """P3. Output is a valid UUID string."""
        result = _deterministic_uuid(_MEDHA_EVENTS_NS, "session-x", "1", "test")
        parsed = uuid.UUID(result)
        assert str(parsed) == result
