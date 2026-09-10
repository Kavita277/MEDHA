"""
MEDHA Backend Dependencies
==========================

FastAPI dependency injection utilities.
Provides shared dependencies such as settings, database sessions, and
logging context.
"""

from __future__ import annotations

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.persistence.database import get_db


def get_app_settings() -> Settings:
    """Dependency for injecting application settings."""
    return get_settings()


__all__ = ["get_app_settings", "get_db"]
