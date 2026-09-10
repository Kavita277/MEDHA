"""
Authentication Pydantic Schemas
===============================

Schemas for authentication requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Payload for authenticating with username/email and password."""
    email: str = Field(..., min_length=3, max_length=255, description="Email or account identifier")
    password: str = Field(..., min_length=1, description="Account password")


class TokenResponse(BaseModel):
    """Access token and user profile returned upon successful authentication."""
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token schema type")
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserResponse = Field(..., description="Authenticated user account details")
