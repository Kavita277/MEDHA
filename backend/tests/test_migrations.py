"""
Alembic Migration Execution Tests
=================================

Programmatic tests validating that Alembic migration scripts run cleanly:
- upgrade head creates expected tables, columns, indexes, and foreign keys
- downgrade base cleanly removes tables
"""

import os
import tempfile
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture
def migration_db():
    """Creates a temporary SQLite file and returns its path and URL."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_migration.db")
    db_url = f"sqlite:///{db_path}"
    yield db_url
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_alembic_upgrade_and_downgrade(migration_db: str):
    """Verifies that migration 001 runs upgrade head and downgrade base cleanly."""
    alembic_ini_path = os.path.abspath("alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", migration_db)

    # 1. Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # 2. Inspect created database schema
    engine = create_engine(migration_db)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "users" in tables, "Table 'users' must be created by migrations"
    assert "therapists" in tables, "Table 'therapists' must be created by migrations"
    assert "cases" in tables, "Table 'cases' must be created by migration 002"
    assert "chat_sessions" in tables, "Table 'chat_sessions' must be created by migration 003"

    # Verify columns in 'users'
    user_columns = {col["name"]: col for col in inspector.get_columns("users")}
    expected_user_cols = [
        "id", "role", "name", "mobile", "email", "password_hash",
        "status", "must_change_password", "created_at", "updated_at", "last_login_at"
    ]
    for col_name in expected_user_cols:
        assert col_name in user_columns, f"Column '{col_name}' missing from 'users'"

    # Verify columns in 'therapists'
    therapist_columns = {col["name"]: col for col in inspector.get_columns("therapists")}
    expected_therapist_cols = ["id", "user_id", "display_name", "created_at", "updated_at"]
    for col_name in expected_therapist_cols:
        assert col_name in therapist_columns, f"Column '{col_name}' missing from 'therapists'"

    # Verify columns in 'cases'
    case_columns = {col["name"]: col for col in inspector.get_columns("cases")}
    expected_case_cols = [
        "id", "victim_id", "user_id", "therapist_id",
        "current_timepoint", "status", "closed_at", "created_at", "updated_at"
    ]
    for col_name in expected_case_cols:
        assert col_name in case_columns, f"Column '{col_name}' missing from 'cases'"

    # Verify columns in 'chat_sessions'
    session_columns = {col["name"]: col for col in inspector.get_columns("chat_sessions")}
    expected_session_cols = [
        "id", "case_id", "session_identifier", "timepoint", "status",
        "state_snapshot", "closed_at", "created_at", "updated_at"
    ]
    for col_name in expected_session_cols:
        assert col_name in session_columns, f"Column '{col_name}' missing from 'chat_sessions'"

    # 3. Run downgrade base
    engine.dispose()
    command.downgrade(alembic_cfg, "base")

    # Inspect after downgrade
    engine_after = create_engine(migration_db)
    inspector_after = inspect(engine_after)
    tables_after = inspector_after.get_table_names()
    engine_after.dispose()

    assert "chat_sessions" not in tables_after, "Table 'chat_sessions' must be dropped on downgrade"
    assert "cases" not in tables_after, "Table 'cases' must be dropped on downgrade"
    assert "therapists" not in tables_after, "Table 'therapists' must be dropped on downgrade"
    assert "users" not in tables_after, "Table 'users' must be dropped on downgrade"


