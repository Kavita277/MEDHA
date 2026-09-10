"""
MEDHA Backend Client — Typed Exceptions
========================================

All exceptions raised by BackendClient are subclasses of MedhaClientError so
callers can catch the entire family with a single except clause if desired.
"""

from __future__ import annotations


class MedhaClientError(Exception):
    """Base exception for all MEDHA backend client errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MedhaAuthError(MedhaClientError):
    """
    Raised when authentication fails (wrong credentials, expired token, etc.).
    HTTP 401 from the backend maps to this.
    """


class MedhaForbiddenError(MedhaClientError):
    """
    Raised when the authenticated user does not have permission for the
    requested resource. HTTP 403 maps to this.
    """


class MedhaNotFoundError(MedhaClientError):
    """
    Raised when the requested resource does not exist (HTTP 404).
    """


class MedhaConflictError(MedhaClientError):
    """
    Raised on conflict (e.g., duplicate session identifier). HTTP 409.
    """


class MedhaServerError(MedhaClientError):
    """
    Raised when the backend returns an unexpected 5xx error.
    """


class MedhaConnectionError(MedhaClientError):
    """
    Raised when the HTTP request cannot reach the backend at all
    (connection refused, timeout, DNS failure, etc.).
    """

    def __init__(self, message: str):
        super().__init__(message, status_code=None)
