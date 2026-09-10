"""
Tests for Behaviour Aggregator
"""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from backend.persistence.models.event import RawEventModel
from backend.services.behaviour.feature_aggregator import BehaviourAggregatorService
from backend.tests.test_sessions_api import session_api_db

@pytest.fixture
def mock_case_id():
    return uuid.uuid4()

@pytest.fixture
def base_time():
    return datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

def test_aggregator_zero_activity(session_api_db):
    engine = session_api_db["engine"]
    case_id = uuid.UUID(session_api_db["case_a_id"])
    
    with Session(engine) as db:
        service = BehaviourAggregatorService(db)
        
        # Aggregate with absolutely no events in DB
        snapshot = service.aggregate_case_timepoint(case_id, timepoint=1)
        
        # Missing data logic expects None
        assert snapshot.app_interaction_duration is None
        assert snapshot.journal_entry_count is None
        assert snapshot.missed_checkin_count is None

def test_aggregator_simple_counts(session_api_db, base_time):
    engine = session_api_db["engine"]
    case_id = uuid.UUID(session_api_db["case_a_id"])
    
    with Session(engine) as db:
        # Insert events for a timepoint
        db.add_all([
            RawEventModel(
                event_id="e1", case_id=case_id, event_type="journal_saved",
                occurred_at=base_time, metadata_payload={"journal_id": "j1"}
            ),
            # Duplicate save for same journal ID
            RawEventModel(
                event_id="e2", case_id=case_id, event_type="journal_saved",
                occurred_at=base_time + timedelta(minutes=5), metadata_payload={"journal_id": "j1"}
            ),
            RawEventModel(
                event_id="e3", case_id=case_id, event_type="chat_message_sent",
                occurred_at=base_time + timedelta(minutes=10), metadata_payload={"role": "user"}
            ),
            # System message should be ignored
            RawEventModel(
                event_id="e4", case_id=case_id, event_type="chat_message_sent",
                occurred_at=base_time + timedelta(minutes=15), metadata_payload={"role": "system"}
            )
        ])
        db.commit()
        
        service = BehaviourAggregatorService(db)
        snapshot = service.aggregate_case_timepoint(case_id, timepoint=1)
        
        # The duplicate journal should only be counted once
        assert snapshot.journal_entry_count == 1.0
        # The system chat message is ignored
        assert snapshot.chat_message_count == 1.0
        # Zero support interactions (since there is activity but no support events, it's 0.0 not None)
        assert snapshot.support_resource_access_count == 0.0

def test_aggregator_temporal_leakage_and_baseline(session_api_db, base_time):
    engine = session_api_db["engine"]
    case_id = uuid.UUID(session_api_db["case_a_id"])
    
    with Session(engine) as db:
        service = BehaviourAggregatorService(db)
        
        t1_start = base_time
        t1_end = base_time + timedelta(hours=12)
        
        # Timepoint 1: duration = 100
        db.add(RawEventModel(event_id="t1_s", case_id=case_id, event_type="session_start", occurred_at=t1_start))
        db.add(RawEventModel(event_id="t1_e", case_id=case_id, event_type="session_end", occurred_at=t1_start + timedelta(seconds=100)))
        db.commit()
        
        s1 = service.aggregate_case_timepoint(case_id, timepoint=1, start_time=t1_start, end_time=t1_end)
        assert s1.app_interaction_duration == 100.0
        assert s1.app_interaction_duration_deviation is None  # Cold start
        
        t2_start = base_time + timedelta(days=1)
        t2_end = base_time + timedelta(days=1, hours=12)
        
        # Timepoint 2: duration = 200
        db.add(RawEventModel(event_id="t2_s", case_id=case_id, event_type="session_start", occurred_at=t2_start))
        db.add(RawEventModel(event_id="t2_e", case_id=case_id, event_type="session_end", occurred_at=t2_start + timedelta(seconds=200)))
        db.commit()
        
        s2 = service.aggregate_case_timepoint(case_id, timepoint=2, start_time=t2_start, end_time=t2_end)
        assert s2.app_interaction_duration == 200.0
        # Deviation Sign Convention Test:
        # V2 Frozen models expect: Deviation = Current - Baseline
        # Baseline = 100 (from T1). Dev = 200 - 100 = 100.0
        assert s2.app_interaction_duration_deviation == 100.0
        
        t3_start = base_time + timedelta(days=2)
        t3_end = base_time + timedelta(days=2, hours=12)
        
        # Timepoint 3: duration = 50
        # Testing negative deviation: 50 - ((100+200)/2) = 50 - 150 = -100.0
        db.add(RawEventModel(event_id="t3_s", case_id=case_id, event_type="session_start", occurred_at=t3_start))
        db.add(RawEventModel(event_id="t3_e", case_id=case_id, event_type="session_end", occurred_at=t3_start + timedelta(seconds=50)))
        db.commit()
        
        s3 = service.aggregate_case_timepoint(case_id, timepoint=3, start_time=t3_start, end_time=t3_end)
        assert s3.app_interaction_duration == 50.0
        # Baseline from T1 (100) + T2 (200) / 2 = 150
        # Dev = 50 - 150 = -100.0
        assert s3.app_interaction_duration_deviation == -100.0
        
        t4_start = base_time + timedelta(days=3)
        t4_end = base_time + timedelta(days=3, hours=12)
        
        # Insert T4 events
        db.add(RawEventModel(event_id="t4_s", case_id=case_id, event_type="session_start", occurred_at=t4_start))
        db.add(RawEventModel(event_id="t4_e", case_id=case_id, event_type="session_end", occurred_at=t4_start + timedelta(seconds=500)))
        db.commit()
        
        # Mandatory temporal leakage test:
        # Re-run T3. Verify T3 hasn't changed despite T4 existing.
        s3_recalc = service.aggregate_case_timepoint(case_id, timepoint=3, start_time=t3_start, end_time=t3_end)
        assert s3_recalc.app_interaction_duration_deviation == -100.0  # Still -100, T4 is ignored

def test_aggregator_checkin_metrics(session_api_db, base_time):
    engine = session_api_db["engine"]
    case_id = uuid.UUID(session_api_db["case_a_id"])
    
    with Session(engine) as db:
        service = BehaviourAggregatorService(db)
        
        db.add_all([
            RawEventModel(event_id="p1", case_id=case_id, event_type="checkin_prompt_shown", occurred_at=base_time),
            RawEventModel(event_id="s1", case_id=case_id, event_type="checkin_completed", occurred_at=base_time + timedelta(seconds=60)),
            
            # Second checkin is prompted but never submitted before next prompt (Missed)
            RawEventModel(event_id="p2", case_id=case_id, event_type="checkin_prompt_shown", occurred_at=base_time + timedelta(hours=1)),
            
            # Third checkin is submitted
            RawEventModel(event_id="p3", case_id=case_id, event_type="checkin_prompt_shown", occurred_at=base_time + timedelta(hours=2)),
            RawEventModel(event_id="s3", case_id=case_id, event_type="checkin_completed", occurred_at=base_time + timedelta(hours=2, seconds=120)),
        ])
        db.commit()
        
        snapshot = service.aggregate_case_timepoint(case_id, timepoint=1)
        
        # 2 completed, 1 missed (p2 overridden by p3). 
        # Delays: 60s and 120s. Avg = 90s.
        assert snapshot.checkin_response_delay == 90.0
        # 3 prompts shown total, 2 completed = 2/3
        assert snapshot.checkin_completion_rate == (2.0 / 3.0)
        assert snapshot.missed_checkin_count == 1.0

def test_aggregator_late_night_usage(session_api_db):
    engine = session_api_db["engine"]
    case_id = uuid.UUID(session_api_db["case_a_id"])
    
    with Session(engine) as db:
        service = BehaviourAggregatorService(db)
        
        db.add_all([
            # 02:00 UTC (Late night)
            RawEventModel(event_id="ln1", case_id=case_id, event_type="chat_message_sent", occurred_at=datetime(2025, 1, 1, 2, 0, tzinfo=timezone.utc)),
            # 05:30 UTC (Late night)
            RawEventModel(event_id="ln2", case_id=case_id, event_type="screen_view", occurred_at=datetime(2025, 1, 1, 5, 30, tzinfo=timezone.utc)),
            # 08:00 UTC (Day)
            RawEventModel(event_id="d1", case_id=case_id, event_type="journal_saved", occurred_at=datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)),
        ])
        db.commit()
        
        snapshot = service.aggregate_case_timepoint(case_id, timepoint=1)
        
        # 2 late night / 3 total = 0.666...
        assert snapshot.late_night_usage_ratio == pytest.approx(2.0 / 3.0)
