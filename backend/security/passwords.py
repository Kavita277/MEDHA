"""
Password Security Utilities
===========================

Secure password hashing and verification using bcrypt.
"""

from __future__ import annotations

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with automated salt generation.
    Returns the decoded UTF-8 hash string.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt()
    pw_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against an existing bcrypt hash string.
    Returns True if valid, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        pw_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except (ValueError, TypeError):
        return False
