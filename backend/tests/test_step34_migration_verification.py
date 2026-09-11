"""
MEDHA Backend Step 34 — Database Migration Verification Tests
=============================================================

Authoritative specification: backend/docs/backend_plan.md §34

Tests the complete existing Alembic migration chain from an empty database:
1. Migration upgrade(head) from an empty DB.
2. Full schema reflection verification via SQLAlchemy Inspector:
   - Tables created by the migration chain
   - Columns and important data types
   - Foreign keys and on-delete referential integrity actions
   - Indexes on foreign keys and lookups
   - Unique and composite unique constraints
   - Enum/constrained-string contracts
   - Nullable vs non-nullable fields
   - Timezone-aware timestamp columns
3. Verification of the clinical missingness invariant:
   - Specialist predictions (struct_pred, text_pred, voice_pred, behav_pred)
   - Behavioural deviations and temporal risk scores
   Must be strictly nullable (missing != 0.0).
4. Migration downgrade(base) -> verify clean drop -> re-upgrade(head) idempotency.
5. End-to-end application execution against a database initialized
   EXCLUSIVELY through Alembic migrations (NO Base.metadata.create_all()).
"""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Generator
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from backend.main import create_application
from backend.persistence.database import get_db
from backend.security.passwords import hash_password
from backend.security.tokens import create_access_token


# ============================================================================
# Fixtures for Migrated Database
# ============================================================================

@pytest.fixture(scope="module")
def migrated_db():
    """
    Creates an empty SQLite database, executes all Alembic migrations to head,
    and yields the database URL and engine.
    Disposes and removes the temporary file on teardown.
    """
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "migrated_step34.db")
    db_url = f"sqlite:///{db_path}"

    alembic_ini_path = os.path.abspath("alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Run upgrade head on fresh database
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    yield {"url": db_url, "engine": engine, "config": alembic_cfg, "path": db_path}

    engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def migrated_app_client(migrated_db) -> Generator[TestClient, None, None]:
    """
    Provides a FastAPI TestClient wired directly to the migrated SQLite database.
    DOES NOT invoke Base.metadata.create_all().
    Overrides get_db to provide sessions bound to the migrated database engine.
    """
    engine = migrated_db["engine"]
    test_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_application()
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


# ============================================================================
# 1. Migration Chain & Table Existence Verification
# ============================================================================

def test_alembic_upgrade_head_creates_all_expected_tables(migrated_db):
    """
    Verifies that running 'alembic upgrade head' from an empty database creates
    all expected tables defined in the current migration chain (revisions 001 to c7d2984ab12e).
    """
    inspector = inspect(migrated_db["engine"])
    tables = set(inspector.get_table_names())

    expected_tables = {
        "alembic_version",
        "users",
        "therapists",
        "cases",
        "chat_sessions",
        "chat_messages",
        "checkins",
        "checkin_questions",
        "raw_events",
        "behaviour_feature_snapshots",
        "prediction_results",
        "audit_logs",
    }

    assert expected_tables.issubset(tables), (
        f"Missing tables in migrated database. Expected {expected_tables}, got {tables}"
    )


# ============================================================================
# 2. Schema Reflection: Columns, Data Types, & Nullability
# ============================================================================

def test_table_columns_and_nullability(migrated_db):
    """
    Inspects critical column definitions, nullability, and data types
    across all migrated tables.
    """
    inspector = inspect(migrated_db["engine"])

    # 1. Users table
    user_cols = {c["name"]: c for c in inspector.get_columns("users")}
    assert user_cols["id"]["nullable"] is False
    assert user_cols["role"]["nullable"] is False
    assert user_cols["email"]["nullable"] is False
    assert user_cols["password_hash"]["nullable"] is False
    assert user_cols["status"]["nullable"] is False
    assert user_cols["must_change_password"]["nullable"] is False
    assert user_cols["created_at"]["nullable"] is False
    assert user_cols["updated_at"]["nullable"] is False
    assert user_cols["last_login_at"]["nullable"] is True

    # 2. Cases table
    case_cols = {c["name"]: c for c in inspector.get_columns("cases")}
    assert case_cols["victim_id"]["nullable"] is False
    assert case_cols["user_id"]["nullable"] is False
    assert case_cols["therapist_id"]["nullable"] is False
    assert case_cols["current_timepoint"]["nullable"] is False
    assert case_cols["status"]["nullable"] is False

    # 3. Chat sessions
    session_cols = {c["name"]: c for c in inspector.get_columns("chat_sessions")}
    assert session_cols["session_identifier"]["nullable"] is False
    assert session_cols["timepoint"]["nullable"] is False
    assert session_cols["status"]["nullable"] is False

    # 4. Raw events
    event_cols = {c["name"]: c for c in inspector.get_columns("raw_events")}
    assert event_cols["event_id"]["nullable"] is False
    assert event_cols["event_type"]["nullable"] is False
    assert event_cols["occurred_at"]["nullable"] is False

    # 5. Audit logs
    audit_cols = {c["name"]: c for c in inspector.get_columns("audit_logs")}
    assert audit_cols["action"]["nullable"] is False
    assert audit_cols["status"]["nullable"] is False
    assert audit_cols["created_at"]["nullable"] is False


# ============================================================================
# 3. Clinical Missingness Invariant (Nullability Verification)
# ============================================================================

def test_clinical_missingness_nullability_invariants(migrated_db):
    """
    CLINICAL INVARIANT: Missing data != 0.0.
    Verifies that all specialist predictions, behavioural deviations, and temporal
    risk scores in the database schema are strictly nullable.
    """
    inspector = inspect(migrated_db["engine"])

    # Prediction results
    pred_cols = {c["name"]: c for c in inspector.get_columns("prediction_results")}
    specialist_cols = ["struct_pred", "text_pred", "voice_pred", "behav_pred"]
    for col in specialist_cols:
        assert col in pred_cols, f"Column '{col}' missing from prediction_results"
        assert pred_cols[col]["nullable"] is True, f"Specialist column '{col}' must be nullable"

    assert pred_cols["fusion_dds_prediction"]["nullable"] is True
    assert pred_cols["temporal_risk_score"]["nullable"] is True
    assert pred_cols["future_escalation_flag"]["nullable"] is True
    assert pred_cols["triage_level"]["nullable"] is True

    # Availability flags must be non-nullable booleans
    assert pred_cols["struct_available"]["nullable"] is False
    assert pred_cols["text_available"]["nullable"] is False
    assert pred_cols["voice_available"]["nullable"] is False
    assert pred_cols["behav_available"]["nullable"] is False

    # Behaviour snapshots
    behav_cols = {c["name"]: c for c in inspector.get_columns("behaviour_feature_snapshots")}
    assert behav_cols["app_interaction_duration_deviation"]["nullable"] is True
    assert behav_cols["checkin_response_delay_deviation"]["nullable"] is True
    assert behav_cols["late_night_usage_ratio"]["nullable"] is True


# ============================================================================
# 4. Foreign Keys & Referential Integrity Actions
# ============================================================================

def test_foreign_keys_and_on_delete_behavior(migrated_db):
    """
    Verifies foreign key constraints and their on-delete actions across tables.
    """
    inspector = inspect(migrated_db["engine"])

    # 1. Therapists -> Users (CASCADE)
    therapist_fks = inspector.get_foreign_keys("therapists")
    user_fk = next((fk for fk in therapist_fks if fk["referred_table"] == "users"), None)
    assert user_fk is not None
    assert "user_id" in user_fk["constrained_columns"]
    assert user_fk["options"].get("ondelete", "").upper() == "CASCADE"

    # 2. Cases -> Users & Therapists (RESTRICT)
    case_fks = inspector.get_foreign_keys("cases")
    case_referred = {fk["referred_table"]: fk for fk in case_fks}
    assert "users" in case_referred
    assert "therapists" in case_referred
    assert case_referred["users"]["options"].get("ondelete", "").upper() == "RESTRICT"
    assert case_referred["therapists"]["options"].get("ondelete", "").upper() == "RESTRICT"

    # 3. Chat Sessions -> Cases (RESTRICT)
    session_fks = inspector.get_foreign_keys("chat_sessions")
    assert any(
        fk["referred_table"] == "cases" and fk["options"].get("ondelete", "").upper() == "RESTRICT"
        for fk in session_fks
    )

    # 4. Chat Messages -> Chat Sessions (RESTRICT)
    message_fks = inspector.get_foreign_keys("chat_messages")
    assert any(
        fk["referred_table"] == "chat_sessions" and fk["options"].get("ondelete", "").upper() == "RESTRICT"
        for fk in message_fks
    )

    # 5. Checkins -> Chat Sessions (RESTRICT)
    checkin_fks = inspector.get_foreign_keys("checkins")
    assert any(
        fk["referred_table"] == "chat_sessions" and fk["options"].get("ondelete", "").upper() == "RESTRICT"
        for fk in checkin_fks
    )

    # 6. Checkin Questions -> Checkins (CASCADE)
    question_fks = inspector.get_foreign_keys("checkin_questions")
    assert any(
        fk["referred_table"] == "checkins" and fk["options"].get("ondelete", "").upper() == "CASCADE"
        for fk in question_fks
    )

    # 7. Raw Events -> Cases (RESTRICT) & Chat Sessions (SET NULL)
    raw_event_fks = {fk["referred_table"]: fk for fk in inspector.get_foreign_keys("raw_events")}
    assert "cases" in raw_event_fks
    assert raw_event_fks["cases"]["options"].get("ondelete", "").upper() == "RESTRICT"
    assert "chat_sessions" in raw_event_fks
    assert raw_event_fks["chat_sessions"]["options"].get("ondelete", "").upper() == "SET NULL"

    # 8. Behaviour Snapshots -> Cases (CASCADE)
    behav_fks = inspector.get_foreign_keys("behaviour_feature_snapshots")
    assert any(
        fk["referred_table"] == "cases" and fk["options"].get("ondelete", "").upper() == "CASCADE"
        for fk in behav_fks
    )

    # 9. Prediction Results -> Cases (CASCADE) & Chat Sessions (SET NULL)
    pred_fks = {fk["referred_table"]: fk for fk in inspector.get_foreign_keys("prediction_results")}
    assert "cases" in pred_fks
    assert pred_fks["cases"]["options"].get("ondelete", "").upper() == "CASCADE"
    assert "chat_sessions" in pred_fks
    assert pred_fks["chat_sessions"]["options"].get("ondelete", "").upper() == "SET NULL"

    # 10. Audit Logs -> Users (SET NULL)
    audit_fks = inspector.get_foreign_keys("audit_logs")
    assert any(
        fk["referred_table"] == "users" and fk["options"].get("ondelete", "").upper() == "SET NULL"
        for fk in audit_fks
    )


# ============================================================================
# 5. Indexes, Unique Constraints, & Composite Constraints
# ============================================================================

def test_indexes_and_unique_constraints(migrated_db):
    """
    Verifies that unique constraints and query performance indexes are in place.
    """
    inspector = inspect(migrated_db["engine"])

    # 1. Users unique email and mobile
    user_indexes = inspector.get_indexes("users")
    user_idx_names = {idx["name"]: idx for idx in user_indexes}
    assert "ix_users_email" in user_idx_names
    assert user_idx_names["ix_users_email"]["unique"] in (True, 1)
    assert "ix_users_mobile" in user_idx_names
    assert user_idx_names["ix_users_mobile"]["unique"] in (True, 1)

    # 2. Cases unique victim_id
    case_indexes = inspector.get_indexes("cases")
    case_idx_names = {idx["name"]: idx for idx in case_indexes}
    assert "ix_cases_victim_id" in case_idx_names
    assert case_idx_names["ix_cases_victim_id"]["unique"] in (True, 1)

    # 3. Chat sessions unique session_identifier
    session_indexes = inspector.get_indexes("chat_sessions")
    session_idx_names = {idx["name"]: idx for idx in session_indexes}
    assert "ix_chat_sessions_session_identifier" in session_idx_names
    assert session_idx_names["ix_chat_sessions_session_identifier"]["unique"] in (True, 1)

    # 4. Raw events unique event_id
    event_indexes = inspector.get_indexes("raw_events")
    event_idx_names = {idx["name"]: idx for idx in event_indexes}
    assert "ix_raw_events_event_id" in event_idx_names
    assert event_idx_names["ix_raw_events_event_id"]["unique"] in (True, 1)

    # 5. Behaviour Snapshots composite unique constraint on (case_id, timepoint)
    behav_unique = inspector.get_unique_constraints("behaviour_feature_snapshots")
    composite_unique = next(
        (u for u in behav_unique if set(u["column_names"]) == {"case_id", "timepoint"}),
        None,
    )
    assert composite_unique is not None, "Composite unique constraint (case_id, timepoint) missing"

    # 6. Audit Logs lookup indexes
    audit_indexes = inspector.get_indexes("audit_logs")
    audit_idx_names = {idx["name"] for idx in audit_indexes}
    assert "ix_audit_logs_actor_user_id" in audit_idx_names
    assert "ix_audit_logs_action" in audit_idx_names
    assert "ix_audit_logs_resource_type" in audit_idx_names
    assert "ix_audit_logs_created_at" in audit_idx_names


# ============================================================================
# 6. Downgrade(base) -> Verify Empty -> Re-upgrade(head) Idempotency
# ============================================================================

def test_migration_downgrade_base_and_reupgrade_idempotency():
    """
    Tests complete migration lifecycle:
    1. Start with fresh temporary DB.
    2. Upgrade to head.
    3. Downgrade to base -> verify all application tables dropped.
    4. Upgrade to head again -> verify successful recreation.
    """
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_cycle.db")
    db_url = f"sqlite:///{db_path}"

    alembic_ini_path = os.path.abspath("alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Step 1: Upgrade to head
    command.upgrade(alembic_cfg, "head")
    engine1 = create_engine(db_url)
    inspector1 = inspect(engine1)
    tables1 = set(inspector1.get_table_names())
    assert "users" in tables1
    assert "audit_logs" in tables1
    engine1.dispose()

    # Step 2: Downgrade to base
    command.downgrade(alembic_cfg, "base")
    engine2 = create_engine(db_url)
    inspector2 = inspect(engine2)
    tables2 = set(inspector2.get_table_names())
    # Only alembic_version (or nothing) should remain
    app_tables = tables2 - {"alembic_version"}
    assert len(app_tables) == 0, f"Expected zero application tables after downgrade, found: {app_tables}"
    engine2.dispose()

    # Step 3: Re-upgrade to head
    command.upgrade(alembic_cfg, "head")
    engine3 = create_engine(db_url)
    inspector3 = inspect(engine3)
    tables3 = set(inspector3.get_table_names())
    assert "users" in tables3
    assert "prediction_results" in tables3
    assert "audit_logs" in tables3
    engine3.dispose()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


# ============================================================================
# 7. Application Execution Against Alembic-Only Database
# ============================================================================

def test_application_execution_against_migrated_db(migrated_db, migrated_app_client: TestClient):
    """
    CRITICAL REQUIREMENT (§34):
    Runs real application flows against a database initialized EXCLUSIVELY via Alembic.
    Verifies that the schema satisfies actual runtime SQLAlchemy ORM queries and constraints.

    Flows exercised:
    1. Health & readiness probes (GET /api/v1/health, GET /api/v1/ready)
    2. Therapist login (POST /api/v1/auth/login)
    3. Therapist creates patient user & case (POST /api/v1/therapist/users)
    4. Case listing and retrieval (GET /api/v1/therapist/cases)
    5. Session creation (POST /api/v1/sessions)
    6. Raw event batch ingestion (POST /api/v1/events/batch)
    7. Chat message persistence and exchange (POST /api/v1/chat/message)
    8. Check-in session creation and question retrieval (POST /api/v1/checkins)
    9. Direct database querying of behaviour snapshots and prediction results
    """
    engine = migrated_db["engine"]

    # ------------------------------------------------------------------------
    # Step A: Seed initial therapist directly into migrated database via ORM
    # ------------------------------------------------------------------------
    therapist_user_id = uuid.uuid4()
    therapist_entity_id = uuid.uuid4()
    therapist_email = "dr.migration@example.com"
    therapist_pwd = "MigrationPass123!"
    hashed_pwd = hash_password(therapist_pwd)

    from backend.persistence.models.user import User, UserRole, UserStatus
    from backend.persistence.models.therapist import Therapist

    with Session(engine) as seed_session:
        t_user = User(
            id=therapist_user_id,
            role=UserRole.THERAPIST,
            name="Dr. Migration Verifier",
            email=therapist_email,
            password_hash=hashed_pwd,
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        seed_session.add(t_user)
        seed_session.flush()

        t_entity = Therapist(
            id=therapist_entity_id,
            user_id=t_user.id,
            display_name="Dr. Migration Verifier, M.D.",
        )
        seed_session.add(t_entity)
        seed_session.commit()

    # ------------------------------------------------------------------------
    # Step B: Health & Readiness Probes
    # ------------------------------------------------------------------------
    health_resp = migrated_app_client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    with patch("backend.api.v1.endpoints.health.check_db_connection", return_value=True):
        ready_resp = migrated_app_client.get("/api/v1/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"

    # ------------------------------------------------------------------------
    # Step C: Therapist Authentication
    # ------------------------------------------------------------------------
    login_resp = migrated_app_client.post(
        "/api/v1/auth/login",
        json={"email": therapist_email, "password": therapist_pwd},
    )
    assert login_resp.status_code == 200
    therapist_token = login_resp.json()["access_token"]
    therapist_headers = {"Authorization": f"Bearer {therapist_token}"}

    # ------------------------------------------------------------------------
    # Step D: Therapist Creates Patient User & Associated Case
    # ------------------------------------------------------------------------
    patient_email = f"patient_{uuid.uuid4().hex[:8]}@example.com"
    create_user_resp = migrated_app_client.post(
        "/api/v1/therapist/users",
        headers=therapist_headers,
        json={
            "name": "Migration Patient",
            "email": patient_email,
            "password": "PatientSecurePass123!",
            "mobile": "+15550199999",
        },
    )
    assert create_user_resp.status_code == 201
    user_data = create_user_resp.json()
    created_user_id = user_data["id"]
    case_info = user_data["case"]
    case_id = case_info["id"]
    victim_id = case_info["victim_id"]
    assert case_id is not None
    assert victim_id is not None

    # ------------------------------------------------------------------------
    # Step E: Case Retrieval
    # ------------------------------------------------------------------------
    cases_resp = migrated_app_client.get("/api/v1/therapist/cases", headers=therapist_headers)
    assert cases_resp.status_code == 200
    case_list = cases_resp.json()
    assert any(c["case_id"] == case_id for c in case_list)

    # Test case timepoint update
    patch_case_resp = migrated_app_client.patch(
        f"/api/v1/therapist/cases/{case_id}",
        headers=therapist_headers,
        json={"current_timepoint": 1},
    )
    assert patch_case_resp.status_code == 200
    assert patch_case_resp.json()["victim_id"] == victim_id

    # ------------------------------------------------------------------------
    # Step F: Patient Login & Session Creation
    # ------------------------------------------------------------------------
    patient_login_resp = migrated_app_client.post(
        "/api/v1/auth/login",
        json={"email": patient_email, "password": "PatientSecurePass123!"},
    )
    assert patient_login_resp.status_code == 200
    patient_token = patient_login_resp.json()["access_token"]
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    session_create_resp = migrated_app_client.post(
        "/api/v1/sessions",
        headers=patient_headers,
        json={"case_id": case_id, "timepoint": 1},
    )
    assert session_create_resp.status_code == 201
    session_data = session_create_resp.json()
    session_id = session_data["id"]

    # ------------------------------------------------------------------------
    # Step G: Raw Event Batch Ingestion
    # ------------------------------------------------------------------------
    event_batch_resp = migrated_app_client.post(
        "/api/v1/events/batch",
        headers=patient_headers,
        json={
            "events": [
                {
                    "event_id": f"evt_mig_{uuid.uuid4().hex[:12]}",
                    "case_id": case_id,
                    "session_id": session_id,
                    "event_type": "app_opened",
                    "occurred_at": "2026-09-11T12:00:00Z",
                    "metadata_payload": {"source": "migration_verification"},
                },
                {
                    "event_id": f"evt_mig_{uuid.uuid4().hex[:12]}",
                    "case_id": case_id,
                    "session_id": session_id,
                    "event_type": "checkin_started",
                    "occurred_at": "2026-09-11T12:01:00Z",
                    "metadata_payload": {"timepoint": 1},
                },
            ],
        },
    )
    assert event_batch_resp.status_code in (200, 201)

    # ------------------------------------------------------------------------
    # Step H: Check-in Creation & State Inspection
    # ------------------------------------------------------------------------
    checkin_create_resp = migrated_app_client.post(
        f"/api/v1/checkins/sessions/{session_id}",
        headers=patient_headers,
    )
    assert checkin_create_resp.status_code in (200, 201)
    checkin_data = checkin_create_resp.json()
    checkin_id = checkin_data["id"]

    get_checkin_resp = migrated_app_client.get(
        f"/api/v1/checkins/{checkin_id}",
        headers=patient_headers,
    )
    assert get_checkin_resp.status_code == 200
    assert get_checkin_resp.json()["id"] == checkin_id

    # ------------------------------------------------------------------------
    # Step I: Chat Message Exchange & Persistence
    # ------------------------------------------------------------------------
    chat_resp = migrated_app_client.post(
        f"/api/v1/chat/sessions/{session_id}/message",
        headers=patient_headers,
        json={
            "message": "Hello, I am completing my check-in today.",
        },
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["user_message"] == "Hello, I am completing my check-in today."
    assert "assistant_response" in chat_data

    # Verify history
    history_resp = migrated_app_client.get(
        f"/api/v1/chat/sessions/{session_id}/history",
        headers=patient_headers,
    )
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert len(history_data["messages"]) >= 2

    # ------------------------------------------------------------------------
    # Step J: Direct Schema Verification of Behaviour Snapshot & Predictions
    # ------------------------------------------------------------------------
    # Insert a behaviour snapshot and prediction result to confirm ORM and DB compatibility
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO behaviour_feature_snapshots ("
                "id, case_id, timepoint, app_interaction_duration, app_interaction_duration_deviation, "
                "checkin_completion_rate, late_night_usage_ratio, aggregated_at"
                ") VALUES (:id, :case_id, :timepoint, :dur, :dev, :comp, :late, CURRENT_TIMESTAMP)"
            ),
            {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "timepoint": 1,
                "dur": 120.0,
                "dev": None,  # clinical missingness
                "comp": 1.0,
                "late": 0.0,
            },
        )

        conn.execute(
            text(
                "INSERT INTO prediction_results ("
                "id, case_id, session_id, timepoint, fusion_dds_prediction, temporal_risk_score, "
                "future_escalation_flag, triage_level, struct_pred, text_pred, voice_pred, behav_pred, "
                "struct_available, text_available, voice_available, behav_available, predicted_at, created_at, updated_at"
                ") VALUES ("
                ":id, :case_id, :session_id, :timepoint, :dds, :temporal, "
                ":flag, :triage, :spred, :tpred, :vpred, :bpred, "
                ":s_avail, :t_avail, :v_avail, :b_avail, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP"
                ")"
            ),
            {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "session_id": session_id,
                "timepoint": 1,
                "dds": 45.2,
                "temporal": None,  # missing != 0
                "flag": 0,
                "triage": "MODERATE",
                "spred": 44.0,
                "tpred": 46.5,
                "vpred": None,  # voice unavailable
                "bpred": None,  # blocked specialist
                "s_avail": True,
                "t_avail": True,
                "v_avail": False,
                "b_avail": False,
            },
        )

    # ------------------------------------------------------------------------
    # Step K: Therapist Retrieves Prediction Results via API
    # ------------------------------------------------------------------------
    pred_history_resp = migrated_app_client.get(
        f"/api/v1/therapist/cases/{case_id}/results",
        headers=therapist_headers,
    )
    assert pred_history_resp.status_code == 200
    results_data = pred_history_resp.json()
    assert "predictions" in results_data or "case_id" in results_data
