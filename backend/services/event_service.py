"""
Event Service
=============

Business logic for behavioral telemetry event ingestion.
Ensures RBAC, case isolation, and delegates idempotent batch inserts to the repository.
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.persistence.models.event import RawEventModel
from backend.persistence.models.user import User, UserRole
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.event import EventRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.schemas.event import EventBatchRequest, EventBatchResponse


# Valid events according to requirements
VALID_EVENT_TYPES = {
    "session_start",
    "session_end",
    "screen_view",
    "checkin_started",
    "checkin_prompt_shown",
    "checkin_answered",
    "checkin_completed",
    "chat_message_sent",
    "journal_opened",
    "journal_saved",
    "voice_started",
    "voice_completed",
    "support_opened",
    "notification_tapped",
    "notification_dismissed",
    "app_backgrounded",
}

class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.case_repo = CaseRepository(db)
        self.therapist_repo = TherapistRepository(db)

    def process_batch(self, payload: EventBatchRequest, current_user: User) -> EventBatchResponse:
        """
        Validates ownership, constructs models, and persists events idempotently.
        """
        if not payload.events:
            return EventBatchResponse(
                status="success",
                received_count=0,
                processed_count=0,
                ignored_duplicate_count=0
            )

        # 1. Group events by case_id for validation efficiency
        case_ids = {event.case_id for event in payload.events}
        
        # 2. Authorize cases
        for case_id in case_ids:
            case = self.case_repo.get(case_id)
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Case {case_id} not found."
                )
            
            if current_user.role == UserRole.USER:
                if case.user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. You can only submit events for your own active case."
                    )
            elif current_user.role == UserRole.THERAPIST:
                therapist = self.therapist_repo.get_by_user_id(current_user.id)
                if not therapist or case.therapist_id != therapist.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. Therapists may only submit events for assigned cases."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized role."
                )

        # 3. Construct persistence models
        db_events: List[RawEventModel] = []
        for event in payload.events:
            db_events.append(
                RawEventModel(
                    event_id=event.event_id,
                    case_id=event.case_id,
                    session_id=event.session_id,
                    event_type=event.event_type,
                    occurred_at=event.occurred_at,
                    metadata_payload=event.metadata_payload,
                )
            )

        # 4. Idempotent insert
        total_received = len(db_events)
        inserted_count = self.event_repo.batch_insert_idempotent(db_events)
        self.db.commit()

        ignored_count = total_received - inserted_count

        return EventBatchResponse(
            status="success",
            received_count=total_received,
            processed_count=inserted_count,
            ignored_duplicate_count=ignored_count
        )
