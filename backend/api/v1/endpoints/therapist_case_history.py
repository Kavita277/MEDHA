"""
Therapist Case History & Clinical Events Endpoints
==================================================

Clinician endpoints for managing patient case histories (demographics,
psychiatric/medical background, medications, treatment goals) and logging
chronological clinical timeline events (milestones, crisis episodes, therapy notes).
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.case import Case
from backend.persistence.models.therapist import Therapist
from backend.persistence.repositories.case_history import (
    CaseHistoryRepository,
    ClinicalEventRepository,
)
from backend.schemas.case_history import (
    CaseHistoryResponse,
    CaseHistoryUpsertRequest,
    ClinicalEventCreateRequest,
    ClinicalEventResponse,
    ClinicalEventUpdateRequest,
)
from backend.security.dependencies import get_current_therapist
from backend.services.audit_service import audit_service

router = APIRouter()


def _get_authorized_case(
    case_id: uuid.UUID,
    current_therapist: Therapist,
    db: Session,
    request: Request | None = None,
) -> Case:
    """Verifies that the requested case exists and is assigned to the authenticated therapist."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None or case.therapist_id != current_therapist.id:
        if request:
            audit_service.log_event(
                db=db,
                action="ACCESS_DENIED",
                actor_user_id=current_therapist.user_id,
                actor_role="therapist",
                resource_type="case",
                resource_id=str(case_id),
                status="DENIED",
                metadata={"reason": "unauthorized_case_history_access"},
                request=request,
            )
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Case does not exist or is not assigned to you.",
        )
    return case


# ---------------------------------------------------------------------------
# Case History Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/cases/{case_id}/history",
    response_model=Optional[CaseHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Patient Case History Profile",
    description="Returns the comprehensive clinical background, intake demographics, psychiatric/medical history, and medications for an assigned patient.",
)
def get_case_history(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> Optional[CaseHistoryResponse]:
    case = _get_authorized_case(case_id, current_therapist, db, request)
    repo = CaseHistoryRepository(db)
    history = repo.get_by_case_id(case.id)
    if history is None:
        return None
    return CaseHistoryResponse.model_validate(history)


@router.put(
    "/cases/{case_id}/history",
    response_model=CaseHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or Update Patient Case History Profile",
    description="Creates or updates the patient's clinical intake, medical/psychiatric history, medications, and treatment goals.",
)
def upsert_case_history(
    case_id: uuid.UUID,
    payload: CaseHistoryUpsertRequest,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseHistoryResponse:
    case = _get_authorized_case(case_id, current_therapist, db, request)
    repo = CaseHistoryRepository(db)
    updated = repo.upsert_for_case(
        case_id=case.id,
        user_id=case.user_id,
        therapist_id=current_therapist.id,
        data=payload.model_dump(exclude_unset=True),
    )

    audit_service.log_event(
        db=db,
        action="CASE_HISTORY_UPDATED",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="case_history",
        resource_id=str(updated.id),
        status="SUCCESS",
        metadata={
            "case_id": str(case.id),
            "victim_id": case.victim_id,
            "primary_diagnosis": updated.primary_diagnosis,
        },
        request=request,
    )
    db.commit()

    return CaseHistoryResponse.model_validate(updated)


# ---------------------------------------------------------------------------
# Clinical Events Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/cases/{case_id}/events",
    response_model=List[ClinicalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Clinical Timeline Events",
    description="Returns chronological clinical events (milestones, crisis episodes, medication changes, session notes) for an assigned case.",
)
def list_clinical_events(
    case_id: uuid.UUID,
    event_type: Optional[str] = Query(None, description="Optional filter by event category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    request: Request = None,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[ClinicalEventResponse]:
    case = _get_authorized_case(case_id, current_therapist, db, request)
    repo = ClinicalEventRepository(db)
    events = repo.list_for_case(case_id=case.id, event_type=event_type, limit=limit, offset=offset)
    return [ClinicalEventResponse.model_validate(e) for e in events]


@router.post(
    "/cases/{case_id}/events",
    response_model=ClinicalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log New Clinical Event",
    description="Logs a new clinical milestone, medication change, crisis episode, or session note for an assigned case.",
)
def create_clinical_event(
    case_id: uuid.UUID,
    payload: ClinicalEventCreateRequest,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> ClinicalEventResponse:
    case = _get_authorized_case(case_id, current_therapist, db, request)
    repo = ClinicalEventRepository(db)
    new_event = repo.create(
        case_id=case.id,
        user_id=case.user_id,
        therapist_id=current_therapist.id,
        data=payload.model_dump(),
    )

    audit_service.log_event(
        db=db,
        action="CLINICAL_EVENT_LOGGED",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="clinical_event",
        resource_id=str(new_event.id),
        status="SUCCESS",
        metadata={
            "case_id": str(case.id),
            "event_type": new_event.event_type,
            "severity": new_event.severity,
            "title": new_event.title,
        },
        request=request,
    )
    db.commit()

    return ClinicalEventResponse.model_validate(new_event)


@router.delete(
    "/cases/{case_id}/events/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Clinical Event",
    description="Removes an erroneously logged clinical event for an assigned case.",
)
def delete_clinical_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> dict:
    case = _get_authorized_case(case_id, current_therapist, db, request)
    repo = ClinicalEventRepository(db)
    success = repo.delete(event_id=event_id, case_id=case.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical event not found for this case.",
        )

    audit_service.log_event(
        db=db,
        action="CLINICAL_EVENT_DELETED",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="clinical_event",
        resource_id=str(event_id),
        status="SUCCESS",
        metadata={"case_id": str(case.id)},
        request=request,
    )
    db.commit()

    return {"status": "deleted", "event_id": str(event_id)}
