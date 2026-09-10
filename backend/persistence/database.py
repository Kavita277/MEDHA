"""
Database Engine & Session Management
====================================

SQLAlchemy 2.0 engine configuration, connection pooling, sessionmaker,
and FastAPI database session dependency.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import Settings, get_settings
from backend.persistence.base import Base

logger = logging.getLogger(__name__)


def build_engine(settings: Optional[Settings] = None) -> Engine:
    """
    Constructs a SQLAlchemy Engine from settings.
    Applies connection pooling, pre-ping liveness checks, and driver-specific options.
    """
    if settings is None:
        settings = get_settings()

    db_uri = settings.SQLALCHEMY_DATABASE_URI
    engine_kwargs: Dict[str, Any] = {
        "echo": settings.DB_ECHO,
    }

    # SQLite specific connection args vs. PostgreSQL connection pooling
    if db_uri.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in db_uri:
            from sqlalchemy.pool import StaticPool
            engine_kwargs["poolclass"] = StaticPool
    else:
        engine_kwargs.update(
            {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_pre_ping": True,
            }
        )

    return create_engine(db_uri, **engine_kwargs)


# Global Engine and SessionLocal factory
engine: Engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding an isolated database session per request.
    Automatically closes the session upon request termination.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(target_engine: Optional[Engine] = None) -> bool:
    """
    Verifies that the database is reachable and accepting queries.
    Returns True if connection succeeds, False otherwise.
    """
    active_engine = target_engine or engine
    try:
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False


def create_all_tables(target_engine: Optional[Engine] = None) -> None:
    """Utility to create all declared tables (used primarily in test suites)."""
    active_engine = target_engine or engine
    Base.metadata.create_all(bind=active_engine)


def drop_all_tables(target_engine: Optional[Engine] = None) -> None:
    """Utility to drop all declared tables (used primarily in test suites)."""
    active_engine = target_engine or engine
    Base.metadata.drop_all(bind=active_engine)
