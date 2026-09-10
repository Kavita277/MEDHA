"""
MEDHA Security Layer
====================

Authentication, authorization, token verification, and encryption utilities.
"""

from backend.security.passwords import hash_password, verify_password
from backend.security.tokens import create_access_token, decode_access_token
from backend.security.dependencies import (
    oauth2_scheme,
    get_current_user,
    require_role,
    get_current_therapist,
    get_current_patient,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "oauth2_scheme",
    "get_current_user",
    "require_role",
    "get_current_therapist",
    "get_current_patient",
]
