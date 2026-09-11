"""
Therapist Results Endpoints (Step 11)
=====================================

Provides secure, therapist-only prediction result APIs.

Authorization Model:
  Every endpoint applies a 3-layer check:
    1. JWT token → valid, non-expired User (401 if absent/invalid)
    2. User.role == THERAPIST → linked Therapist profile (403 if not)
    3. case.therapist_id == current_therapist.id (403 if mismatch)

  Patients (USER role) receive 403 at step 2.
  An unauthenticated request receives 401.
  A therapist requesting another therapist's case data receives 403.

Information Leakage Prevention:
  When a case does not exist OR belongs to a different therapist, the
  response is always 403 (not 404). This prevents enumeration attacks
  where an attacker could distinguish "does not exist" from "exists but
  forbidden". The only exception is when the case is genuinely not found
  for the requesting therapist — see _get_authorized_case().

  Session ownership verification always checks:
    session → case → therapist
  Never trusting only the session_id.

Missing Prediction Semantics:
  If no prediction exists for a case, the endpoint returns HTTP 200 with
  results_available=False and all prediction fields null. This is NOT an
  error state. The client must distinguish "results not yet available" from
  a real prediction result.

Step 10 Note:
  behav_pred is always null. The Frozen V2 Behaviour Specialist integration
  (Step 10) is blocked because the Engagement_Score data generator was not
  recovered. behav_available is always False. Do not remove this note when
  Step 10 is unblocked — update it instead.
"""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from backend.dependencies import get_db
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.user import User
from backend.persistence.models.checkin import CheckInModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.persistence.repositories.prediction_result import PredictionResultRepository
from datetime import datetime, timezone
from backend.schemas.voice import VoiceRecordReviewResponse
from backend.schemas.results import (
    CaseSummaryResponse,
    CaseResultResponse,
    SessionSummaryResponse,
    SpecialistPredictionsResponse,
    CheckinSummaryResponse,
    CheckinQuestionItemResponse,
    BehaviourSummaryResponse,
    AlertSummaryResponse,
    AlertHandleRequest,
    AlertHandleResponse,
)
from backend.security.dependencies import get_current_therapist
from backend.services.triage_service import compute_triage_level, TRIAGE_LEVEL_UNKNOWN
from backend.services.audit_service import audit_service

router = APIRouter()



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_BEHAV_BLOCKED_REASON = (
    "Frozen V2 Behaviour Specialist integration is blocked: "
    "Engagement_Score original data generator was not recovered (Step 9C). "
    "The ML team must provide the generator script or retrain with Step 9A event metrics."
)


def _get_authorized_case(
    case_id: uuid.UUID,
    current_therapist: Therapist,
    db: Session,
    request: Request | None = None,
) -> Case:
    """
    Retrieves a Case and verifies it belongs to the requesting therapist.

    Returns HTTP 403 (not 404) regardless of whether the case exists but
    belongs to another therapist, to prevent case-ID enumeration.
    Logs an ACCESS_DENIED audit event on failure without altering the 403 response.
    """
    case_repo = CaseRepository(db)
    case = case_repo.get(case_id)
    if case is None or case.therapist_id != current_therapist.id:
        audit_service.log_event(
            db=db,
            action="ACCESS_DENIED",
            actor_user_id=current_therapist.user_id,
            actor_role="therapist",
            resource_type="case",
            resource_id=str(case_id),
            status="DENIED",
            metadata={"case_id": str(case_id), "reason": "unauthorized_or_not_found"},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Case not found or access denied.",
        )
    return case



def _build_result_response(
    case: Case,
    prediction: "PredictionResultModel | None",
    session_id: "uuid.UUID | None" = None,
) -> CaseResultResponse:
    """
    Builds a CaseResultResponse from a Case and an optional PredictionResultModel.

    When prediction is None (no record exists), returns results_available=False
    with all prediction fields null and triage UNKNOWN.
    """
    # Resolve patient info from case relationship
    user: User = case.user

    if prediction is None:
        return CaseResultResponse(
            case_id=case.id,
            victim_id=case.victim_id,
            user_id=case.user_id,
            session_id=session_id,
            timepoint=case.current_timepoint,
            results_available=False,
            fusion_dds_prediction=None,
            temporal_risk_score=None,
            future_escalation_flag=None,
            triage_level=TRIAGE_LEVEL_UNKNOWN,
            specialists=SpecialistPredictionsResponse(
                struct_pred=None,
                text_pred=None,
                voice_pred=None,
                behav_pred=None,
                struct_available=False,
                text_available=False,
                voice_available=False,
                behav_available=False,
                behav_blocked=True,
                behav_block_reason=_BEHAV_BLOCKED_REASON,
            ),
            predicted_at=None,
            result_record_created_at=None,
        )

    # Compute or use stored triage level
    triage = prediction.triage_level or compute_triage_level(
        fusion_dds=prediction.fusion_dds_prediction,
        temporal_risk=prediction.temporal_risk_score,
    )

    return CaseResultResponse(
        case_id=case.id,
        victim_id=case.victim_id,
        user_id=case.user_id,
        session_id=prediction.session_id,
        timepoint=prediction.timepoint,
        results_available=True,
        fusion_dds_prediction=prediction.fusion_dds_prediction,
        temporal_risk_score=prediction.temporal_risk_score,
        future_escalation_flag=prediction.future_escalation_flag,
        triage_level=triage,
        specialists=SpecialistPredictionsResponse(
            struct_pred=prediction.struct_pred,
            text_pred=prediction.text_pred,
            voice_pred=prediction.voice_pred,
            # behav_pred always null: Step 10 blocked
            behav_pred=prediction.behav_pred,
            struct_available=prediction.struct_available,
            text_available=prediction.text_available,
            voice_available=prediction.voice_available,
            # behav_available always False until Step 10 resolved
            behav_available=prediction.behav_available,
            behav_blocked=True,
            behav_block_reason=_BEHAV_BLOCKED_REASON,
        ),
        predicted_at=prediction.predicted_at,
        result_record_created_at=prediction.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/cases",
    response_model=List[CaseSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Therapist's Cases",
    description=(
        "Returns all cases assigned to the authenticated therapist. "
        "Strictly isolated: cannot see cases belonging to other therapists. "
        "Patients (USER role) receive 403."
    ),
)
def list_therapist_cases(
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[CaseSummaryResponse]:
    """Returns all cases belonging to the authenticated therapist."""
    case_repo = CaseRepository(db)
    cases = case_repo.list_cases_for_therapist(current_therapist.id)

    results = []
    for case in cases:
        user: User = case.user
        results.append(
            CaseSummaryResponse(
                case_id=case.id,
                victim_id=case.victim_id,
                user_id=case.user_id,
                status=case.status,
                current_timepoint=case.current_timepoint,
                patient_name=user.name,
                patient_email=user.email,
                case_created_at=case.created_at,
            )
        )
    return results


@router.get(
    "/cases/{case_id}/results",
    response_model=CaseResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest Prediction Results for a Case",
    description=(
        "Returns the latest MEDHA prediction result for the specified case. "
        "If no prediction has been computed yet, returns results_available=False "
        "with all prediction fields null. Never returns fabricated scores. "
        "Strict ownership: therapist must own the case."
    ),
)
def get_case_results(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseResultResponse:
    """Returns the latest prediction result for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    pred_repo = PredictionResultRepository(db)
    prediction = pred_repo.get_latest_for_case(case.id)

    audit_service.log_event(
        db=db,
        action="THERAPIST_VIEWED_PREDICTION",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="case",
        resource_id=str(case.id),
        status="SUCCESS",
        metadata={
            "results_available": prediction is not None,
            "timepoint": case.current_timepoint,
        },
        request=request,
    )
    db.commit()

    return _build_result_response(case=case, prediction=prediction)


@router.get(
    "/cases/{case_id}/sessions",
    response_model=List[SessionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Sessions for a Case",
    description=(
        "Returns all sessions belonging to the specified case. "
        "Therapist must own the case. Patients receive 403."
    ),
)
def list_case_sessions(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[SessionSummaryResponse]:
    """Returns all sessions for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    session_repo = SessionRepository(db)
    sessions = session_repo.list_for_case(case.id)

    return [
        SessionSummaryResponse(
            session_id=sess.id,
            session_identifier=sess.session_identifier,
            timepoint=sess.timepoint,
            status=sess.status,
            closed_at=sess.closed_at,
            created_at=sess.created_at,
        )
        for sess in sessions
    ]


@router.get(
    "/sessions/{session_id}/results",
    response_model=CaseResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest Prediction Results for a Session",
    description=(
        "Returns the latest MEDHA prediction result associated with a specific session. "
        "Authorization chain: session → case → therapist. "
        "Never authorized based on session_id alone. "
        "If no prediction exists for this session, returns results_available=False."
    ),
)
def get_session_results(
    session_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> CaseResultResponse:
    """
    Returns the latest prediction result for a session, with full ownership verification.

    Authorization chain verified:
      1. session exists
      2. session.case_id → case exists
      3. case.therapist_id == current_therapist.id
    """
    session_repo = SessionRepository(db)
    session: SessionModel | None = session_repo.get(session_id)

    if session is None:
        audit_service.log_event(
            db=db,
            action="ACCESS_DENIED",
            actor_user_id=current_therapist.user_id,
            actor_role="therapist",
            resource_type="session",
            resource_id=str(session_id),
            status="DENIED",
            metadata={"session_id": str(session_id), "reason": "session_not_found"},
            request=request,
        )
        db.commit()
        # Return 403 not 404 to prevent session-ID enumeration
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not found or access denied.",
        )

    # Verify ownership through the case
    case = _get_authorized_case(session.case_id, current_therapist, db, request=request)

    pred_repo = PredictionResultRepository(db)
    prediction = pred_repo.get_latest_for_session(session.id)

    audit_service.log_event(
        db=db,
        action="THERAPIST_VIEWED_PREDICTION",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="session",
        resource_id=str(session.id),
        status="SUCCESS",
        metadata={
            "case_id": str(case.id),
            "results_available": prediction is not None,
            "timepoint": session.timepoint,
        },
        request=request,
    )
    db.commit()

    return _build_result_response(case=case, prediction=prediction, session_id=session.id)


_CHECKIN_DOMAIN_MAP = {
    "GW": "General Wellbeing & Mood",
    "SF": "Sleep & Daytime Functioning",
    "ES": "Stress & Coping",
    "SA": "Safety & Stability",
    "SE": "Social Support & Connection",
}


@router.get(
    "/cases/{case_id}/checkins",
    response_model=List[CheckinSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Check-ins for a Case",
    description="Returns all historical check-ins for the specified case. Therapist must own the case.",
)
def list_case_checkins(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[CheckinSummaryResponse]:
    """Returns all historical check-ins for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    checkins = (
        db.query(CheckInModel)
        .options(joinedload(CheckInModel.questions))
        .join(SessionModel)
        .filter(SessionModel.case_id == case.id)
        .order_by(CheckInModel.created_at.desc())
        .all()
    )

    results = []
    for c in checkins:
        q_items = []
        for q in (c.questions or []):
            prefix = q.question_id.split("-")[0] if "-" in q.question_id else q.question_id[:2]
            domain = _CHECKIN_DOMAIN_MAP.get(prefix, "Clinical Assessment")
            q_items.append(
                CheckinQuestionItemResponse(
                    question_id=q.question_id,
                    question_text=q.question_text,
                    domain=domain,
                    answer=q.answer,
                    answer_status=q.answer_status,
                    answered_at=q.answered_at,
                )
            )
        results.append(
            CheckinSummaryResponse(
                checkin_id=c.id,
                timepoint=c.session.timepoint,
                status=c.status,
                started_at=c.created_at,
                completed_at=c.completed_at,
                questions=q_items,
            )
        )
    return results


@router.get(
    "/cases/{case_id}/behaviour",
    response_model=List[BehaviourSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Behaviour History for a Case",
    description="Returns longitudinal behaviour features for the specified case. Therapist must own the case.",
)
def list_case_behaviour(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[BehaviourSummaryResponse]:
    """Returns historical behaviour snapshots for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    snapshots = (
        db.query(BehaviourFeatureSnapshotModel)
        .filter(BehaviourFeatureSnapshotModel.case_id == case.id)
        .order_by(BehaviourFeatureSnapshotModel.timepoint.desc())
        .all()
    )

    return [
        BehaviourSummaryResponse(
            timepoint=s.timepoint,
            app_interaction_duration=s.app_interaction_duration,
            checkin_completion_rate=s.checkin_completion_rate,
            missed_checkin_count=s.missed_checkin_count,
            computed_at=s.aggregated_at,
        )
        for s in snapshots
    ]


@router.get(
    "/cases/{case_id}/alerts",
    response_model=List[AlertSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Safety Alerts for a Case",
    description="Returns all safety alerts associated with the specified case. Therapist must own the case.",
)
def list_case_alerts(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[AlertSummaryResponse]:
    """Returns all safety alerts for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    alerts = (
        db.query(SafetyEventModel)
        .filter(SafetyEventModel.case_id == case.id)
        .order_by(SafetyEventModel.detected_at.desc())
        .all()
    )

    audit_service.log_event(
        db=db,
        action="THERAPIST_VIEWED_ALERT",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="case",
        resource_id=str(case.id),
        status="SUCCESS",
        metadata={"alert_count": len(alerts)},
        request=request,
    )
    db.commit()

    return [
        AlertSummaryResponse(
            id=a.id,
            event_type=a.event_type,
            severity=a.severity,
            status=a.status,
            detected_at=a.detected_at,
            handled_by=a.handled_by,
            handled_at=a.handled_at,
        )
        for a in alerts
    ]


@router.patch(
    "/cases/{case_id}/alerts/{alert_id}",
    response_model=AlertHandleResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle / Resolve a Safety Alert",
    description="Allows a therapist to handle or update the resolution status of an active safety alert for an assigned case.",
)
def handle_case_alert(
    case_id: uuid.UUID,
    alert_id: uuid.UUID,
    payload: AlertHandleRequest,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> AlertHandleResponse:
    """Updates safety alert lifecycle status and records audit event."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    alert: SafetyEventModel | None = (
        db.query(SafetyEventModel)
        .filter(SafetyEventModel.id == alert_id, SafetyEventModel.case_id == case.id)
        .first()
    )

    if alert is None:
        audit_service.log_event(
            db=db,
            action="ACCESS_DENIED",
            actor_user_id=current_therapist.user_id,
            actor_role="therapist",
            resource_type="alert",
            resource_id=str(alert_id),
            status="DENIED",
            metadata={"case_id": str(case_id), "alert_id": str(alert_id), "reason": "alert_not_found_or_foreign_case"},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert not found or access denied.",
        )

    alert.status = payload.status
    if payload.status.lower() in ("handled", "resolved", "dismissed"):
        alert.handled_by = current_therapist.user_id
        alert.handled_at = datetime.now(timezone.utc)

    audit_service.log_event(
        db=db,
        action="ALERT_HANDLED",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="alert",
        resource_id=str(alert.id),
        status="SUCCESS",
        metadata={
            "case_id": str(case.id),
            "event_type": alert.event_type,
            "severity": alert.severity,
            "new_status": alert.status,
        },
        request=request,
    )
    db.commit()
    db.refresh(alert)

    return AlertHandleResponse.model_validate(alert)


@router.get(
    "/cases/{case_id}/voice-records",
    response_model=List[VoiceRecordReviewResponse],
    status_code=status.HTTP_200_OK,
    summary="List Voice Records for a Case",
    description="Returns all historical voice check-in recordings, extracted acoustic features, and predictions for clinician review. Therapist must own the case.",
)
def list_case_voice_records(
    case_id: uuid.UUID,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[VoiceRecordReviewResponse]:
    """Returns all historical voice check-in records for a therapist-owned case."""
    case = _get_authorized_case(case_id, current_therapist, db, request=request)

    records = (
        db.query(VoiceRecordModel)
        .filter(VoiceRecordModel.case_id == case.id)
        .order_by(VoiceRecordModel.created_at.desc())
        .all()
    )

    return [VoiceRecordReviewResponse.model_validate(r) for r in records]




