"""
JWT Token Utilities
===================

Token generation, signing, and verification using pyjwt.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import jwt

from backend.config import get_settings


def create_access_token(
    subject: Optional[Union[str, uuid.UUID]] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
    *,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Creates and signs a JWT access token containing standard and domain claims.
    Accepts either (subject, role, ...) or (data={...}, ...).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims: Dict[str, Any] = {}
    if data:
        claims.update(data)

    sub = str(subject) if subject is not None else str(claims.pop("sub", ""))
    token_role = str(role) if role is not None else str(claims.pop("role", "USER"))

    payload: Dict[str, Any] = {
        "sub": sub,
        "role": token_role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": uuid.uuid4().hex,
    }

    # Add extra claims
    payload.update(claims)
    if extra_claims:
        payload.update(extra_claims)

    encoded = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token signature, expiration, and payload.
    Raises jwt.PyJWTError if invalid or expired.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat", "role"]},
    )
    return payload
