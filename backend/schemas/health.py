"""
Health and Readiness Schemas
============================

Data transfer objects for health and readiness endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel, Field


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


class HealthResponse(BaseModel):
    """Schema for basic liveness/health probe."""

    status: str = Field(default="ok", description="Liveness status indicator")
    service: str = Field(default="MEDHA Backend API", description="Service name")
    version: str = Field(description="Application version")
    environment: str = Field(description="Active environment profile")
    timestamp: datetime = Field(default_factory=_current_utc, description="Current UTC timestamp")


class ReadinessResponse(BaseModel):
    """Schema for readiness probe verifying dependencies and subsystem status."""

    status: str = Field(default="ready", description="Readiness status indicator")
    service: str = Field(default="MEDHA Backend API", description="Service name")
    version: str = Field(description="Application version")
    environment: str = Field(description="Active environment profile")
    timestamp: datetime = Field(default_factory=_current_utc, description="Current UTC timestamp")
    checks: Dict[str, str] = Field(
        default_factory=dict, description="Health status of internal subsystems"
    )
