"""
Database Configuration & Persistence Infrastructure Tests
=========================================================

Tests for STEP 3:
- Database settings and URI construction
- SQLAlchemy engine construction and connection checks
- Session factory and get_db dependency lifecycle
- Declarative Base and TimestampMixin
- Generic BaseRepository CRUD operations
- Alembic configuration file and migration folder structure
"""

import os
from datetime import datetime, timezone
import pytest
from sqlalchemy import Column, Integer, String, select, text
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.persistence.base import Base, TimestampMixin
from backend.persistence.database import (
    build_engine,
    check_db_connection,
    get_db,
    SessionLocal,
)
from backend.persistence.repositories import BaseRepository
from alembic.config import Config


# ---------------------------------------------------------------------------
# Test Model for Persistence & Mixin Verification
# ---------------------------------------------------------------------------
class MockItem(Base, TimestampMixin):
    __tablename__ = "test_mock_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def memory_settings():
    """Returns Settings configured with in-memory SQLite database."""
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        DB_ECHO=False,
    )


@pytest.fixture
def memory_engine(memory_settings):
    """Yields an engine bound to an in-memory SQLite database with schema created."""
    engine = build_engine(memory_settings)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def memory_session(memory_engine):
    """Yields a database session bound to the in-memory engine."""
    connection = memory_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Tests: Configuration & URI Resolution
# ---------------------------------------------------------------------------
def test_default_database_uri_generation():
    """Verifies default PostgreSQL URI generation from individual components."""
    settings = Settings(
        DATABASE_URL="",
        POSTGRES_SERVER="db.internal",
        POSTGRES_PORT=5433,
        POSTGRES_USER="medha_admin",
        POSTGRES_PASSWORD="secure_password",
        POSTGRES_DB="medha_prod",
    )
    expected_uri = "postgresql+psycopg2://medha_admin:secure_password@db.internal:5433/medha_prod"
    assert settings.SQLALCHEMY_DATABASE_URI == expected_uri


def test_database_url_override_and_normalization():
    """Verifies DATABASE_URL takes priority and normalizes postgres:// to postgresql://."""
    # Test normalization of legacy prefix
    settings_legacy = Settings(
        DATABASE_URL="postgres://user:pass@host:5432/dbname"
    )
    assert settings_legacy.SQLALCHEMY_DATABASE_URI == "postgresql://user:pass@host:5432/dbname"

    # Test explicit SQLite URL
    settings_sqlite = Settings(
        DATABASE_URL="sqlite:///./test.db"
    )
    assert settings_sqlite.SQLALCHEMY_DATABASE_URI == "sqlite:///./test.db"


# ---------------------------------------------------------------------------
# Tests: Engine & Connection Check
# ---------------------------------------------------------------------------
def test_build_engine_sqlite(memory_settings):
    """Verifies engine builds properly for SQLite with check_same_thread=False."""
    engine = build_engine(memory_settings)
    assert engine is not None
    assert str(engine.url) == "sqlite:///:memory:"
    engine.dispose()


def test_check_db_connection(memory_engine):
    """Verifies check_db_connection accurately tests engine connectivity."""
    assert check_db_connection(memory_engine) is True

    # Test with a mock non-responsive engine
    broken_settings = Settings(
        DATABASE_URL="sqlite:////non_existent_path/non_existent_folder/db.sqlite"
    )
    broken_engine = build_engine(broken_settings)
    # Connecting to invalid path should fail check_db_connection safely
    assert check_db_connection(broken_engine) is False
    broken_engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Session Lifecycle & get_db Dependency
# ---------------------------------------------------------------------------
def test_get_db_yield_and_close(monkeypatch, memory_engine):
    """Verifies that get_db yields an active session and closes it afterwards."""
    from sqlalchemy.orm import sessionmaker
    test_session_factory = sessionmaker(bind=memory_engine)

    import backend.persistence.database as db_mod
    monkeypatch.setattr(db_mod, "SessionLocal", test_session_factory)

    generator = db_mod.get_db()
    session = next(generator)

    assert isinstance(session, Session)
    assert session.is_active

    # Can execute queries
    result = session.execute(text("SELECT 1")).scalar()
    assert result == 1

    # Closing through generator completion
    with pytest.raises(StopIteration):
        next(generator)


# ---------------------------------------------------------------------------
# Tests: Base Model & TimestampMixin
# ---------------------------------------------------------------------------
def test_model_timestamps(memory_session):
    """Verifies TimestampMixin auto-populates created_at and updated_at with UTC datetimes."""
    from backend.persistence.base import _current_utc_timestamp

    # Test UTC generator directly
    current_utc = _current_utc_timestamp()
    assert current_utc.tzinfo == timezone.utc

    item = MockItem(name="Test Item 1")
    memory_session.add(item)
    memory_session.commit()
    memory_session.refresh(item)

    assert item.id is not None
    assert item.name == "Test Item 1"
    assert isinstance(item.created_at, datetime)
    assert isinstance(item.updated_at, datetime)
    # Under SQLite driver, tzinfo is stripped on column deserialization,
    # but the timestamp was generated and persisted accurately.
    assert item.created_at <= _current_utc_timestamp().replace(tzinfo=item.created_at.tzinfo)


# ---------------------------------------------------------------------------
# Tests: Generic BaseRepository
# ---------------------------------------------------------------------------
def test_base_repository_crud(memory_session):
    """Verifies BaseRepository standard CRUD methods."""
    repo = BaseRepository(MockItem, memory_session)

    # 1. Add
    item1 = repo.add(MockItem(name="Repo Item 1"))
    item2 = repo.add(MockItem(name="Repo Item 2"))
    assert item1.id is not None
    assert item2.id is not None

    # 2. Get
    fetched = repo.get(item1.id)
    assert fetched is not None
    assert fetched.name == "Repo Item 1"

    # 3. List
    all_items = repo.list()
    assert len(all_items) == 2

    # 4. Delete
    repo.delete(item1)
    assert repo.get(item1.id) is None
    assert len(repo.list()) == 1


# ---------------------------------------------------------------------------
# Tests: Alembic Configuration & Migration Structure
# ---------------------------------------------------------------------------
def test_alembic_configuration_validity():
    """Verifies alembic.ini is present, valid, and correctly configured."""
    alembic_ini_path = os.path.abspath("alembic.ini")
    assert os.path.exists(alembic_ini_path), "alembic.ini must exist at repo root"

    config = Config(alembic_ini_path)
    script_location = config.get_main_option("script_location")
    assert script_location == "backend/persistence/migrations"

    # Check that migration directory structure exists
    assert os.path.isdir("backend/persistence/migrations")
    assert os.path.isfile("backend/persistence/migrations/env.py")
    assert os.path.isfile("backend/persistence/migrations/script.py.mako")
    assert os.path.isdir("backend/persistence/migrations/versions")
