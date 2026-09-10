"""
Security Utilities Tests
========================

Unit tests verifying password hashing, verification, and JWT token lifecycle.
"""

from datetime import timedelta
import time
import jwt
import pytest

from backend.config import Settings
from backend.security.passwords import hash_password, verify_password
from backend.security.tokens import create_access_token, decode_access_token


def test_password_hashing_and_verification():
    """Verifies bcrypt hashing, verification, and non-reversibility."""
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    # 1. Hash is not plaintext
    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # 2. Correct password verifies
    assert verify_password(raw_password, hashed) is True

    # 3. Incorrect password fails
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False

    # 4. Salts are unique per hash
    second_hash = hash_password(raw_password)
    assert hashed != second_hash
    assert verify_password(raw_password, second_hash) is True


def test_jwt_token_generation_and_decoding():
    """Verifies JWT token encoding, claim extraction, and expiration handling."""
    data = {
        "sub": "user-uuid-12345",
        "role": "THERAPIST",
        "email": "therapist@medha.org",
    }

    # 1. Standard token generation
    token = create_access_token(data=data, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    # 2. Decode claims
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-uuid-12345"
    assert decoded["role"] == "THERAPIST"
    assert decoded["email"] == "therapist@medha.org"
    assert "exp" in decoded

    # 3. Expired token raises ExpiredSignatureError
    expired_token = create_access_token(data=data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)

    # 4. Tampered token raises InvalidTokenError
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)
