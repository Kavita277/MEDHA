"""
Case History & Clinical Event Repositories
===========================================

SQLAlchemy database access layers for CaseHistoryModel and ClinicalEventModel.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.persistence.models.case_history import CaseHistoryModel
from backend.persistence.models.clinical_event import ClinicalEventModel


class CaseHistoryRepository:
    """Repository managing patient clinical case history profiles."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_case_id(self, case_id: uuid.UUID) -> Optional[CaseHistoryModel]:
        """Fetches the unique clinical case history profile for a given case."""
        stmt = select(CaseHistoryModel).where(CaseHistoryModel.case_id == case_id)
        return self.db.execute(stmt).scalars().first()

    def upsert_for_case(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        therapist_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> CaseHistoryModel:
        """
        Creates or updates the CaseHistoryModel for the specified case.
        """
        existing = self.get_by_case_id(case_id)
        if existing is None:
            existing = CaseHistoryModel(
                id=uuid.uuid4(),
                case_id=case_id,
                user_id=user_id,
                therapist_id=therapist_id,
            )
            self.db.add(existing)

        # Update fields provided in data
        for key, value in data.items():
            if hasattr(existing, key) and key not in ("id", "case_id", "user_id", "created_at"):
                setattr(existing, key, value)

        existing.therapist_id = therapist_id
        existing.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(existing)
        return existing


class ClinicalEventRepository:
    """Repository managing chronological clinical milestones and events."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_case(
        self,
        case_id: uuid.UUID,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ClinicalEventModel]:
        """Lists events for a case ordered chronologically (newest first)."""
        stmt = select(ClinicalEventModel).where(ClinicalEventModel.case_id == case_id)
        if event_type:
            stmt = stmt.where(ClinicalEventModel.event_type == event_type)
        stmt = stmt.order_by(desc(ClinicalEventModel.occurred_at), desc(ClinicalEventModel.created_at))
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, event_id: uuid.UUID) -> Optional[ClinicalEventModel]:
        """Retrieves a single clinical event by its primary key."""
        stmt = select(ClinicalEventModel).where(ClinicalEventModel.id == event_id)
        return self.db.execute(stmt).scalars().first()

    def create(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        therapist_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> ClinicalEventModel:
        """Creates and persists a new clinical event."""
        occurred_at = data.get("occurred_at") or datetime.now(timezone.utc)
        new_event = ClinicalEventModel(
            id=uuid.uuid4(),
            case_id=case_id,
            user_id=user_id,
            therapist_id=therapist_id,
            title=data["title"],
            event_type=data.get("event_type", "SESSION_NOTE"),
            severity=data.get("severity", "MEDIUM"),
            occurred_at=occurred_at,
            description=data["description"],
            action_taken=data.get("action_taken"),
            metadata_payload=data.get("metadata_payload"),
        )
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)
        return new_event

    def update(
        self,
        event_id: uuid.UUID,
        case_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> Optional[ClinicalEventModel]:
        """Updates an existing clinical event ensuring it belongs to the case."""
        event = self.get_by_id(event_id)
        if event is None or event.case_id != case_id:
            return None

        for key, value in data.items():
            if hasattr(event, key) and key not in ("id", "case_id", "user_id", "therapist_id", "created_at"):
                if value is not None:
                    setattr(event, key, value)

        event.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event_id: uuid.UUID, case_id: uuid.UUID) -> bool:
        """Deletes a clinical event ensuring it belongs to the case."""
        event = self.get_by_id(event_id)
        if event is None or event.case_id != case_id:
            return False

        self.db.delete(event)
        self.db.commit()
        return True
