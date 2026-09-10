"""
Events Endpoints
================
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.persistence.database import get_db
from backend.security.dependencies import get_current_user
from backend.services.event_service import EventService
from backend.schemas.event import EventBatchRequest, EventBatchResponse
from backend.persistence.models.user import User

router = APIRouter()


@router.post("/batch", response_model=EventBatchResponse, status_code=status.HTTP_201_CREATED)
def submit_events_batch(
    request: EventBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits a batch of telemetry events.
    Events are processed idempotently (duplicate event_ids are ignored).
    """
    service = EventService(db)
    return service.process_batch(request, current_user)
