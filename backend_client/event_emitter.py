"""
MEDHA Backend Event Emitter
=============================

Constructs and submits raw behaviour events from the Streamlit app to the
backend's `POST /api/v1/events/batch` endpoint.

Design:
  - Called once per chat turn to emit telemetry collected by the Streamlit app.
  - Events are idempotent by design (duplicate event_ids are ignored by the server).
  - event_ids are UUIDv4 generated deterministically from (session_id, turn_index,
    event_type) so re-renders of the Streamlit page don't double-submit.
  - No direct database access — this module only calls BackendClient.submit_events().
  - Does NOT compute behaviour features. It emits raw events; the backend
    Step 9A aggregator computes derived features later.

Events emitted per turn:
  1. session_start  — emitted only on the very first turn (turn_index == 1)
  2. chat_message_sent — emitted on every turn

Additional events called explicitly by app.py:
  3. session_end — called when user clicks "New Conversation" or closes
  4. screen_view — optionally called when app renders a new page
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend_client.client import MedhaBackendClient
from backend_client.exceptions import MedhaClientError


def _deterministic_uuid(namespace: str, *parts: str) -> str:
    """
    Generates a deterministic UUIDv5 from a namespace and ordered string parts.
    Using UUIDv5 ensures idempotency: the same (session_id, turn, event_type)
    always produces the same event_id, so backend deduplication works correctly
    even if the Streamlit app re-renders or the user retries.
    """
    seed = ":".join(parts)
    return str(uuid.uuid5(uuid.UUID(namespace), seed))


# Stable namespace UUID for MEDHA event IDs (arbitrary, must not change)
_MEDHA_EVENTS_NS = "b45c9f2a-e3d1-4c8b-9f7e-2a1b3c4d5e6f"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackendEventEmitter:
    """
    Constructs raw MEDHA behaviour events from app-level telemetry and submits
    them to the backend in a single batch per turn.

    Parameters
    ----------
    client:
        Instantiated MedhaBackendClient.
    session_id:
        Backend session UUID string. Used as event namespace and for dedup.
    silent:
        If True, swallow submission errors silently (default True).
        The chatbot must not be blocked by event ingestion failures.
    """

    def __init__(
        self,
        client: MedhaBackendClient,
        session_id: str,
        silent: bool = True,
    ):
        self._client = client
        self._session_id = session_id
        self._silent = silent

    def _make_event(
        self,
        event_type: str,
        occurred_at: Optional[str],
        turn_index: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Constructs a single raw event dict for submission."""
        event_id = _deterministic_uuid(
            _MEDHA_EVENTS_NS,
            self._session_id,
            str(turn_index),
            event_type,
        )
        return {
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": occurred_at or _now_iso(),
            "metadata": metadata or {},
        }

    def emit_turn(
        self,
        token: str,
        turn_index: int,
        occurred_at: Optional[str] = None,
        session_duration_seconds: float = 0.0,
        message_length: int = 0,
        safety_triggered: bool = False,
    ) -> None:
        """
        Emits events for a completed chat turn.

        Emits:
          - session_start (only on turn_index == 1)
          - chat_message_sent

        Parameters
        ----------
        token:
            Bearer JWT for the authenticated user.
        turn_index:
            1-indexed turn counter from ConversationManager.
        occurred_at:
            ISO-8601 timestamp of the turn. Defaults to now().
        session_duration_seconds:
            Elapsed seconds since session creation.
        message_length:
            Length of the user message in characters.
        safety_triggered:
            Whether the safety gateway triggered on this turn.
        """
        ts = occurred_at or _now_iso()
        events: List[Dict[str, Any]] = []

        # 1. session_start — first turn only
        if turn_index == 1:
            events.append(
                self._make_event(
                    event_type="session_start",
                    occurred_at=ts,
                    turn_index=0,  # turn 0 = session lifecycle events
                    metadata={"session_id": self._session_id},
                )
            )

        # 2. chat_message_sent
        events.append(
            self._make_event(
                event_type="chat_message_sent",
                occurred_at=ts,
                turn_index=turn_index,
                metadata={
                    "session_duration_seconds": round(session_duration_seconds, 1),
                    "message_length_chars": message_length,
                    "safety_triggered": safety_triggered,
                    "turn_index": turn_index,
                },
            )
        )

        self._submit(token, events)

    def emit_session_end(self, token: str, occurred_at: Optional[str] = None) -> None:
        """
        Emits a session_end event. Called when the user ends or restarts a session.

        Parameters
        ----------
        token:
            Bearer JWT.
        occurred_at:
            ISO-8601 timestamp. Defaults to now().
        """
        events = [
            self._make_event(
                event_type="session_end",
                occurred_at=occurred_at or _now_iso(),
                turn_index=0,
                metadata={"session_id": self._session_id},
            )
        ]
        self._submit(token, events)

    def emit_screen_view(
        self,
        token: str,
        screen_name: str,
        occurred_at: Optional[str] = None,
    ) -> None:
        """
        Emits a screen_view event.

        Parameters
        ----------
        token:
            Bearer JWT.
        screen_name:
            Logical name of the screen being viewed (e.g. 'chat', 'checkin').
        occurred_at:
            ISO-8601 timestamp. Defaults to now().
        """
        events = [
            self._make_event(
                event_type="screen_view",
                occurred_at=occurred_at or _now_iso(),
                turn_index=0,
                metadata={"screen": screen_name},
            )
        ]
        self._submit(token, events)

    def _submit(self, token: str, events: List[Dict[str, Any]]) -> None:
        """
        Submits events. Swallows errors silently when self._silent=True
        so that event ingestion failures never block the chatbot.
        """
        if not events:
            return
        try:
            self._client.submit_events(token=token, events=events)
        except MedhaClientError:
            if not self._silent:
                raise
        except Exception:
            if not self._silent:
                raise
