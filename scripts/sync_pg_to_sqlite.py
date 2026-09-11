"""
Sync all data from PostgreSQL to local SQLite medha.db.
Allows inspecting the database either in SQLite (medha.db) or PostgreSQL.
"""
from backend.persistence.base import Base
from backend.persistence.database import engine as pg_engine
from backend.persistence.models import (
    User,
    Therapist,
    Case,
    SessionModel,
    CheckInModel,
    QuestionRecordModel,
    PredictionResultModel,
    VoiceRecordModel,
    JournalEntryModel,
    RawEventModel,
    SafetyEventModel,
    AuditLogModel,
    BehaviourFeatureSnapshotModel,
)
from sqlalchemy import create_engine, MetaData, Table, select
import uuid
import json

sqlite_engine = create_engine("sqlite:///./medha.db")

# Create all tables in SQLite
Base.metadata.create_all(bind=sqlite_engine)

tables = [
    "users",
    "therapists",
    "cases",
    "chat_sessions",
    "checkins",
    "checkin_questions",
    "prediction_results",
    "voice_records",
    "journal_entries",
    "raw_events",
    "safety_events",
    "audit_logs",
    "behaviour_feature_snapshots",
]

with pg_engine.connect() as pg_conn, sqlite_engine.begin() as sqlite_conn:
    for table_name in tables:
        try:
            pg_table = Table(table_name, MetaData(), autoload_with=pg_engine)
            sqlite_table = Table(table_name, MetaData(), autoload_with=sqlite_engine)
            
            # Fetch from PG
            rows = pg_conn.execute(select(pg_table)).mappings().all()
            
            # Clear existing SQLite table
            sqlite_conn.execute(sqlite_table.delete())
            
            if rows:
                clean_rows = []
                for r in rows:
                    row_dict = dict(r)
                    for k, v in row_dict.items():
                        if isinstance(v, uuid.UUID):
                            row_dict[k] = str(v)
                        elif isinstance(v, (dict, list)):
                            row_dict[k] = json.dumps(v)
                    clean_rows.append(row_dict)
                sqlite_conn.execute(sqlite_table.insert(), clean_rows)
                print(f"Synced {len(clean_rows)} rows to SQLite '{table_name}'")
            else:
                print(f"Table '{table_name}' has 0 rows.")
        except Exception as e:
            print(f"Error syncing {table_name}: {e}")

print("\nDatabase sync from PostgreSQL to medha.db completed successfully!")
