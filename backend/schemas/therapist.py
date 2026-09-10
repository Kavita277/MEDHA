"""
Therapist Pydantic Schemas
==========================

Schemas for therapist profile creation, updating, and reading.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.user import UserResponse


class TherapistBase(BaseModel):
    """Shared attributes for therapist schemas."""
    display_name: str = Field(..., min_length=1, max_length=255, description="Clinician display name")


class TherapistCreate(TherapistBase):
    """Payload for creating a therapist profile."""
    user_id: uuid.UUID = Field(..., description="ID of the authenticated user with THERAPIST role")


class TherapistUpdate(BaseModel):
    """Payload for updating therapist profile information."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)


class TherapistResponse(TherapistBase):
    """Serialized representation of a therapist profile."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
