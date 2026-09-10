"""
MEDHA Persistence Infrastructure
================================

SQLAlchemy 2.0 database engine, declarative Base, session lifecycle,
and repository patterns.
"""

from backend.persistence.base import Base, TimestampMixin
from backend.persistence.database import (
    SessionLocal,
    build_engine,
    check_db_connection,
    create_all_tables,
    drop_all_tables,
    engine,
    get_db,
)
from backend.persistence.repositories import BaseRepository

__all__ = [
    "Base",
    "TimestampMixin",
    "engine",
    "SessionLocal",
    "build_engine",
    "get_db",
    "check_db_connection",
    "create_all_tables",
    "drop_all_tables",
    "BaseRepository",
]
