"""
User Pydantic Schemas
=====================

Schemas for user creation, reading, and update payloads.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.persistence.models.user import UserRole, UserStatus

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$")


class UserBase(BaseModel):
    """Shared attributes for user schemas."""
    email: str = Field(..., min_length=5, max_length=255, description="User's unique email address")
    name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    mobile: Optional[str] = Field(None, max_length=32, description="Contact mobile number")
    role: UserRole = Field(default=UserRole.USER, description="User role in the system")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Account operational status")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError(f"Invalid email address format: '{v}'")
        return clean


class UserCreate(UserBase):
    """Payload for registering a new user."""
    password: str = Field(..., min_length=8, description="Raw initial password to be hashed")
    must_change_password: bool = Field(default=False, description="Flag requiring password update on first login")


class UserUpdate(BaseModel):
    """Payload for updating user profile or state."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    mobile: Optional[str] = Field(None, max_length=32)
    status: Optional[UserStatus] = None
    must_change_password: Optional[bool] = None
    last_login_at: Optional[datetime] = None


class UserResponse(UserBase):
    """Serialized representation of an existing user."""
    id: uuid.UUID
    must_change_password: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
