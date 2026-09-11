"""
Therapist Recommendations & Safety Protocol Endpoints (Step 26)
===============================================================

Provides secure, clinician-only endpoints for clinical recommendations, tailored
self-help materials, and evaluated dynamic safety protocols.

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
from backend.schemas.recommendations import (
    CaseRecommendationsResponse,
    SafetyProtocolResponse,
)
from backend.security.dependencies import get_current_therapist
from backend.services.recommendation_service import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


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
    "/cases/{case_id}/recommendations",
    response_model=CaseRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical Recommendations for a Case",
    description=(
        "Returns rank-ordered clinical decision support recommendations, self-help resources, "
        "and dynamic safety protocol evaluation for the specified case. "
        "Strict ownership: requesting therapist must own the case."
    ),
)
def get_case_recommendations(
    case_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseRecommendationsResponse:
    """Returns clinical recommendations for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db)
    return recommendation_service.get_case_recommendations(db=db, case=case)


@router.get(
    "/sessions/{session_id}/recommendations",
    response_model=CaseRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical Recommendations for a Session",
    description=(
        "Returns clinical recommendations for a specific session with full authorization chain. "
        "Authorization chain: session → case → therapist."
    ),
)
def get_session_recommendations(
    session_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseRecommendationsResponse:
    """Returns clinical recommendations for a session, verifying full authorization chain."""
    session_repo = SessionRepository(db)
    session: SessionModel | None = session_repo.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not found or access denied.",
        )

    case = _get_authorized_case(session.case_id, current_therapist, db)
    return recommendation_service.get_case_recommendations(db=db, case=case, session_id=session.id)


@router.get(
    "/cases/{case_id}/safety-protocol",
    response_model=SafetyProtocolResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Evaluated Safety Protocol for a Case",
    description=(
        "Evaluates and returns dynamic safety alert protocol, reason codes, and CTAs for a case. "
        "Strict ownership: requesting therapist must own the case."
    ),
)
def get_case_safety_protocol(
    case_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> SafetyProtocolResponse:
    """Returns evaluated safety protocol for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db)
    return recommendation_service.get_safety_protocol(db=db, case=case)


@router.get(
    "/sessions/{session_id}/safety-protocol",
    response_model=SafetyProtocolResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Evaluated Safety Protocol for a Session",
    description=(
        "Evaluates dynamic safety protocol for a specific session. "
        "Authorization chain: session → case → therapist."
    ),
)
def get_session_safety_protocol(
    session_id: uuid.UUID,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> SafetyProtocolResponse:
    """Returns evaluated safety protocol for a session, verifying full authorization chain."""
    session_repo = SessionRepository(db)
    session: SessionModel | None = session_repo.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not found or access denied.",
        )

    case = _get_authorized_case(session.case_id, current_therapist, db)
    return recommendation_service.get_safety_protocol(db=db, case=case, session_id=session.id)
