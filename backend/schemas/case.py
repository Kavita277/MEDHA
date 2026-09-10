"""
Case Pydantic Schemas
=====================

Schemas for case management and therapist patient operations.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.schemas.user import UserResponse

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$")


class CaseBase(BaseModel):
    """Shared case attributes."""
    victim_id: str = Field(..., max_length=100, description="Unique longitudinal identifier for V2 pipeline")
    current_timepoint: int = Field(default=1, ge=1, le=10, description="Current check-in timepoint index")
    status: str = Field(default="active", max_length=32, description="Case lifecycle status")


class CaseCreate(BaseModel):
    """Payload for creating a new case."""
    victim_id: Optional[str] = Field(None, max_length=100, description="Optional custom victim identifier")
    user_id: uuid.UUID = Field(..., description="Patient user account UUID")
    therapist_id: uuid.UUID = Field(..., description="Clinician profile UUID")
    current_timepoint: int = Field(default=1, ge=1, le=10)


class CaseResponse(CaseBase):
    """Serialized representation of a case."""
    id: uuid.UUID
    user_id: uuid.UUID
    therapist_id: uuid.UUID
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TherapistCreateUserRequest(BaseModel):
    """Payload when an authenticated therapist creates a new patient user account and linked case."""
    name: str = Field(..., min_length=1, max_length=255, description="Patient full name")
    email: str = Field(..., min_length=5, max_length=255, description="Patient email address")
    password: str = Field(..., min_length=8, description="Initial temporary/permanent password")
    mobile: Optional[str] = Field(None, max_length=32, description="Contact mobile number")
    victim_id: Optional[str] = Field(None, max_length=100, description="Optional custom victim_id")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError(f"Invalid email address format: '{v}'")
        return clean


class TherapistUserResponse(UserResponse):
    """Patient user profile along with linked case details."""
    case: Optional[CaseResponse] = None

    model_config = ConfigDict(from_attributes=True)

