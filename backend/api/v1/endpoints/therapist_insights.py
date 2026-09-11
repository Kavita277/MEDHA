"""
Therapist Insights Endpoints (Step 25)
======================================

Provides secure, clinician-only endpoints for explainability and clinical insights.

Authorization Model:
  Every endpoint applies a 3-layer check:
    1. JWT token → valid, non-expired User (401 if absent/invalid)
    2. User.role == THERAPIST → linked Therapist profile (403 if not)
    3. case.therapist_id == current_therapist.id (403 if mismatch)

  Patients (USER role) receive 403.
  An unauthenticated request receives 401.
  A therapist requesting another therapist's case data receives 403 (anti-enumeration).

Session Ownership Verification:
  session → case → therapist
  Never trusting only the session_id.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.therapist import Therapist
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.schemas.insights import CaseInsightsResponse
from backend.security.dependencies import get_current_therapist
from backend.services.insights_service import InsightService

router = APIRouter()
insight_service = InsightService()


def _get_authorized_case(
    case_id: uuid.UUID,
    current_therapist: Therapist,
    db: Session,
) -> Case:
    """
    Retrieves a Case and verifies it belongs to the requesting therapist.
    Returns HTTP 403 (not 404) on mismatch to prevent case-ID enumeration.
    """
    case_repo = CaseRepository(db)
    case = case_repo.get(case_id)
    if case is None or case.therapist_id != current_therapist.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Case not found or access denied.",
        )
    return case


@router.get(
    "/cases/{case_id}/insights",
    response_model=CaseInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical Insights for a Case",
    description=(
        "Returns deterministic, support-oriented clinical insights and factor "
        "breakdowns for the specified case. If no prediction is available, returns "
        "results_available=False with safe observational summary. "
        "Strict ownership: requesting therapist must own the case."
    ),
)
def get_case_insights(
    case_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseInsightsResponse:
    """Returns clinical insights for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db)
    return insight_service.get_case_insights(db=db, case=case)


@router.get(
    "/sessions/{session_id}/insights",
    response_model=CaseInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical Insights for a Session",
    description=(
        "Returns clinical insights for a specific session with full ownership verification. "
        "Authorization chain: session → case → therapist."
    ),
)
def get_session_insights(
    session_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseInsightsResponse:
    """Returns clinical insights for a session, verifying full authorization chain."""
    session_repo = SessionRepository(db)
    session: SessionModel | None = session_repo.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not found or access denied.",
        )

    case = _get_authorized_case(session.case_id, current_therapist, db)
    return insight_service.get_case_insights(db=db, case=case, session_id=session.id)
