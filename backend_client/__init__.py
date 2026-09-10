"""
MEDHA Backend Client
====================

Public interface for the backend_client package.
"""

from backend_client.client import (
    MedhaBackendClient,
    LoginResult,
    SessionResult,
    ChatTurnResult,
    ChatMessage,
    EventSubmitResult,
)
from backend_client.event_emitter import BackendEventEmitter
from backend_client.exceptions import (
    MedhaClientError,
    MedhaAuthError,
    MedhaForbiddenError,
    MedhaNotFoundError,
    MedhaConflictError,
    MedhaServerError,
    MedhaConnectionError,
)

__all__ = [
    # Client
    "MedhaBackendClient",
    # Result types
    "LoginResult",
    "SessionResult",
    "ChatTurnResult",
    "ChatMessage",
    "EventSubmitResult",
    # Event emitter
    "BackendEventEmitter",
    # Exceptions
    "MedhaClientError",
    "MedhaAuthError",
    "MedhaForbiddenError",
    "MedhaNotFoundError",
    "MedhaConflictError",
    "MedhaServerError",
    "MedhaConnectionError",
]
