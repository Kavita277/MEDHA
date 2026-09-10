"""
Therapist Results Schemas
==========================

Pydantic schemas for the Therapist Results API (Step 11).

Design Contract:
  - All prediction fields are Optional. null means GENUINELY UNAVAILABLE.
  - MISSING != ZERO. Never fabricate predictions.
  - behav_pred remains null (Step 10 blocked) until Behaviour Specialist
    integration is resolved.
  - These schemas must NEVER leak: model internals, weights, file paths,
    database PKs for unrelated entities, or another therapist's data.
  - results_available = False ⟹ all prediction fields should be null.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.triage_service import ALL_TRIAGE_LEVELS


# ---------------------------------------------------------------------------
# Case summary (lightweight, for case list endpoint)
# ---------------------------------------------------------------------------

class CaseSummaryResponse(BaseModel):
    """
    Compact case/patient summary for the therapist's patient list.
    Contains enough information for a dashboard row without sensitive extras.
    """
    case_id: uuid.UUID = Field(..., description="Unique case identifier")
    victim_id: str = Field(..., description="External victim identifier for V2 pipeline")
    user_id: uuid.UUID = Field(..., description="Associated patient user ID")
    status: str = Field(..., description="Case lifecycle status (active/closed)")
    current_timepoint: int = Field(..., description="Current timepoint index")
    patient_name: str = Field(..., description="Patient display name")
    patient_email: str = Field(..., description="Patient email address")
    case_created_at: datetime = Field(..., description="When the case was opened")

    model_config = ConfigDict(from_attributes=False)


# ---------------------------------------------------------------------------
# Session summary (for session-list endpoint)
# ---------------------------------------------------------------------------

class SessionSummaryResponse(BaseModel):
    """
    Compact session summary for the therapist's session list under a case.
    """
    session_id: uuid.UUID = Field(..., description="Session UUID")
    session_identifier: str = Field(..., description="Human-readable session identifier")
    timepoint: int = Field(..., description="Session timepoint")
    status: str = Field(..., description="Session lifecycle status")
    closed_at: Optional[datetime] = Field(None, description="When session ended (null if active)")
    created_at: datetime = Field(..., description="Session creation timestamp")
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Therapist Historical Data Schemas
# ---------------------------------------------------------------------------

class CheckinSummaryResponse(BaseModel):
    """
    Compact checkin summary for historical view.
    """
    checkin_id: uuid.UUID = Field(..., description="Check-in ID")
    timepoint: int = Field(..., description="Timepoint of the check-in")
    status: str = Field(..., description="Lifecycle status (e.g., completed)")
    started_at: datetime = Field(..., description="When check-in was started")
    completed_at: Optional[datetime] = Field(None, description="When check-in was completed")

    model_config = ConfigDict(from_attributes=True)


class BehaviourSummaryResponse(BaseModel):
    """
    Historical behaviour snapshot for a given timepoint.
    """
    timepoint: int = Field(..., description="Timepoint of the behaviour snapshot")
    app_interaction_duration: Optional[float] = Field(None, description="App Interaction Duration")
    checkin_completion_rate: Optional[float] = Field(None, description="Checkin Completion Rate")
    missed_checkin_count: Optional[int] = Field(None, description="Missed Checkin Count")
    computed_at: datetime = Field(..., description="When the features were aggregated")

    model_config = ConfigDict(from_attributes=True)

class AlertSummaryResponse(BaseModel):
    """
    Compact safety alert for historical view.
    """
    id: uuid.UUID = Field(..., description="Alert ID")
    event_type: str = Field(..., description="Type of alert (e.g., self_harm_intent)")
    severity: str = Field(..., description="Severity of the alert")
    status: str = Field(..., description="Lifecycle status (active/resolved)")
    detected_at: datetime = Field(..., description="When the alert was detected")
    handled_by: Optional[uuid.UUID] = Field(None, description="Therapist who handled the alert")
    handled_at: Optional[datetime] = Field(None, description="When the alert was handled")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Specialist prediction block
# ---------------------------------------------------------------------------

class SpecialistPredictionsResponse(BaseModel):
    """
    Block of specialist predictions. All values are nullable (missing != zero).

    Behav_Pred remains null because Step 10 (Frozen V2 Behaviour Specialist
    integration) is intentionally blocked. The original Engagement_Score
    data generator was not recovered; see STEP_9C report for details.
    """
    struct_pred: Optional[float] = Field(
        None,
        description="Structured specialist prediction (0–100). Null = unavailable.",
    )
    text_pred: Optional[float] = Field(
        None,
        description="Text modality prediction (0–100). Null = unavailable.",
    )
    voice_pred: Optional[float] = Field(
        None,
        description="Voice modality prediction (0–100). Null = unavailable.",
    )
    behav_pred: Optional[float] = Field(
        None,
        description=(
            "Behaviour modality prediction (0–100). "
            "CURRENTLY UNAVAILABLE: Step 10 (Frozen V2 Behaviour Specialist integration) "
            "is blocked because the original Engagement_Score data generator was not recovered. "
            "This field will remain null until Step 10 is resolved."
        ),
    )

    # Availability flags
    struct_available: bool = Field(
        False,
        description="True if structured modality prediction is populated.",
    )
    text_available: bool = Field(
        False,
        description="True if text modality prediction is populated.",
    )
    voice_available: bool = Field(
        False,
        description="True if voice modality prediction is populated.",
    )
    behav_available: bool = Field(
        False,
        description=(
            "True if behaviour modality prediction is populated. "
            "Always False until Step 10 is unblocked."
        ),
    )

    # Behaviour block status (informational, not a prediction)
    behav_blocked: bool = Field(
        True,
        description=(
            "True while the Frozen V2 Behaviour Specialist integration is blocked. "
            "This is an engineering status field, not a clinical signal."
        ),
    )
    behav_block_reason: str = Field(
        (
            "Frozen V2 Behaviour Specialist integration is blocked: "
            "Engagement_Score original data generator was not recovered (Step 9C). "
            "The ML team must provide the generator script or retrain with Step 9A event metrics."
        ),
        description="Human-readable explanation of the behaviour block.",
    )


# ---------------------------------------------------------------------------
# Core result response
# ---------------------------------------------------------------------------

class CaseResultResponse(BaseModel):
    """
    Full MEDHA prediction result for a given case.

    Returned by:
      GET /api/v1/therapist/cases/{case_id}/results
      GET /api/v1/therapist/sessions/{session_id}/results

    When no prediction exists, results_available=False and all prediction
    fields are null. This is NOT an error; it is the correct semantic for
    a case that has not yet been scored.
    """

    # Identity
    case_id: uuid.UUID = Field(..., description="Case this result belongs to")
    victim_id: str = Field(..., description="External victim identifier")
    user_id: uuid.UUID = Field(..., description="Patient user ID")
    session_id: Optional[uuid.UUID] = Field(
        None,
        description="Session this result is associated with (null = case-level result)",
    )
    timepoint: Optional[int] = Field(
        None,
        description="Timepoint at which prediction was made",
    )

    # Availability sentinel
    results_available: bool = Field(
        ...,
        description=(
            "True if at least one prediction has been computed and stored for this case. "
            "False if the case has never been scored."
        ),
    )

    # Core V2 outputs (all nullable)
    fusion_dds_prediction: Optional[float] = Field(
        None,
        description="Fusion DDS (0–100). Null = unavailable.",
        ge=0.0,
        le=100.0,
    )
    temporal_risk_score: Optional[float] = Field(
        None,
        description="GRU temporal risk probability (0–1). Null = insufficient history.",
        ge=0.0,
        le=1.0,
    )
    future_escalation_flag: Optional[int] = Field(
        None,
        description="1 = future escalation predicted, 0 = safe. Null = unavailable.",
    )
    triage_level: str = Field(
        "UNKNOWN",
        description=f"Triage level. One of {ALL_TRIAGE_LEVELS}.",
    )

    # Specialist predictions
    specialists: SpecialistPredictionsResponse = Field(
        ...,
        description="Block of specialist modality predictions.",
    )

    # Timestamps
    predicted_at: Optional[datetime] = Field(
        None,
        description="When the prediction was generated. Null if no prediction exists.",
    )
    result_record_created_at: Optional[datetime] = Field(
        None,
        description="When the result record was persisted. Null if no prediction exists.",
    )

    model_config = ConfigDict(from_attributes=False)
