"""
Feature Aggregator Service
==========================
Orchestrates raw event ingestion to exactly 10 authoritative behaviour features.
Ensures idempotency, accurate T-1 baselining, and missing data semantics.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models.event import RawEventModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.services.behaviour.schemas import BehaviourFeatureSnapshot

from backend.services.behaviour.event_mapping import (
    calculate_app_interaction_duration,
    calculate_checkin_metrics,
    calculate_simple_counts,
    calculate_late_night_ratio
)
from backend.services.behaviour.baseline import calculate_all_deviations


class BehaviourAggregatorService:
    def __init__(self, db: Session):
        self.db = db

    def aggregate_case_timepoint(
        self, 
        case_id: uuid.UUID, 
        timepoint: int, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> BehaviourFeatureSnapshot:
        """
        Main orchestration function to deterministically calculate the 10 features for a timepoint.
        """
        
        # 1. Fetch raw events bounded by time (if bounds provided) and deduplicate them by event_id.
        stmt = select(RawEventModel).where(RawEventModel.case_id == case_id)
        if start_time:
            stmt = stmt.where(RawEventModel.occurred_at >= start_time)
        if end_time:
            stmt = stmt.where(RawEventModel.occurred_at < end_time)
            
        raw_events = self.db.execute(stmt).scalars().all()
        
        # Deduplicate by event_id and sort chronologically
        unique_events = {}
        for ev in raw_events:
            unique_events[ev.event_id] = ev
        sorted_events = sorted(unique_events.values(), key=lambda x: x.occurred_at)
        
        # 2. Extract Base Features from Events
        duration = calculate_app_interaction_duration(sorted_events)
        checkin_metrics = calculate_checkin_metrics(sorted_events)
        simple_counts = calculate_simple_counts(sorted_events)
        late_night_ratio = calculate_late_night_ratio(sorted_events)
        
        # 3. Fetch STRICTLY PAST snapshots for baseline deviation
        past_stmt = select(BehaviourFeatureSnapshotModel).where(
            BehaviourFeatureSnapshotModel.case_id == case_id,
            BehaviourFeatureSnapshotModel.timepoint < timepoint
        )
        past_snapshots = self.db.execute(past_stmt).scalars().all()
        
        # 4. Calculate Deviations
        duration_dev, delay_dev = calculate_all_deviations(
            current_duration=duration,
            current_delay=checkin_metrics["Checkin_Response_Delay"],
            past_snapshots=past_snapshots
        )
        
        # 5. Construct Final Snapshot Schema
        snapshot_dto = BehaviourFeatureSnapshot(
            app_interaction_duration=duration,
            app_interaction_duration_deviation=duration_dev,
            checkin_response_delay=checkin_metrics["Checkin_Response_Delay"],
            checkin_response_delay_deviation=delay_dev,
            checkin_completion_rate=checkin_metrics["Checkin_Completion_Rate"],
            missed_checkin_count=checkin_metrics["Missed_Checkin_Count"],
            journal_entry_count=simple_counts["Journal_Entry_Count"],
            chat_message_count=simple_counts["Chat_Message_Count"],
            late_night_usage_ratio=late_night_ratio,
            support_resource_access_count=simple_counts["Support_Resource_Access_Count"],
        )
        
        # 6. Persist / Update the DB Snapshot
        existing_stmt = select(BehaviourFeatureSnapshotModel).where(
            BehaviourFeatureSnapshotModel.case_id == case_id,
            BehaviourFeatureSnapshotModel.timepoint == timepoint
        )
        existing = self.db.execute(existing_stmt).scalars().first()
        
        if existing:
            # Update
            for k, v in snapshot_dto.model_dump().items():
                setattr(existing, k, v)
        else:
            # Insert
            new_snapshot = BehaviourFeatureSnapshotModel(
                case_id=case_id,
                timepoint=timepoint,
                **snapshot_dto.model_dump()
            )
            self.db.add(new_snapshot)
            
        self.db.commit()
        
        return snapshot_dto
