"""
Therapist Recommendations & Safety Protocol Schemas
===================================================

Pydantic schemas for the Therapist Clinical Recommendation and Safety Protocol Engine API (Step 26).

Design Contract:
  - Adapts outputs from the authoritative, frozen MEDHA Recommendation Engine
    (`engine/recommendation_engine/`) and Alert Engine (`engine/alert_engine/`).
  - Strict human-in-the-loop decision support framing: non-diagnostic observations
    and clinical decision support actions only.
  - Transparent data provenance: clear distinction between distress/risk and safety.
  - Conversational safety fast-path is preserved.
  - Never leaks internal model weights or unauthorized case data.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecommendationItem(BaseModel):
    """
    Individual structured intervention recommendation.
    """
    id: str = Field(..., description="Unique recommendation rule/item identifier")
    category: str = Field(..., description="Intervention category (e.g. monitoring, counselling, protection, legal_support)")
    priority: str = Field(..., description="Priority level (IMMEDIATE, URGENT, PRIORITY, INCREASED, ROUTINE)")
    reason: str = Field(..., description="Clinical decision support rationale for the recommendation")
    action: str = Field(..., description="Recommended supportive action or referral step")

    model_config = ConfigDict(from_attributes=True)


class SelfHelpResourceItem(BaseModel):
    """
    Tailored self-help or psychoeducational resource.
    """
    id: str = Field(..., description="Resource identifier")
    type: str = Field(..., description="Resource type (e.g. guide, exercise, contact, article)")
    title: str = Field(..., description="Display title of the self-help resource")
    category: str = Field(..., description="Topic category (e.g. grounding, safety, legal, sleep)")
    description: str = Field(..., description="Brief description of the resource")

    model_config = ConfigDict(from_attributes=True)


class SafetyProtocolResponse(BaseModel):
    """
    Evaluated dynamic safety alert / safety protocol payload derived from the Alert Engine.
    """
    alert_id: str = Field(..., description="Deterministic alert identifier")
    case_id: uuid.UUID = Field(..., description="Case identifier")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID if session-specific")
    alert_triggered: bool = Field(..., description="True if alert criteria were met, False for routine monitoring")
    priority: str = Field(..., description="Alert priority (IMMEDIATE, URGENT, PRIORITY, ATTENTION, ROUTINE)")
    alert_type: str = Field(..., description="Alert category (CRISIS_ESCALATION, SAFETY_ESCALATION, SUPPORT_RISK, SUPPORT_NOTIFICATION, MONITORING)")
    title: str = Field(..., description="Summary alert title")
    message: str = Field(..., description="Support-oriented descriptive notification message")
    recommended_action: str = Field(..., description="Recommended clinician action")
    cta: str = Field(..., description="Call-to-Action button text")
    reason: str = Field(..., description="Primary reason summary")
    source: str = Field("fusion_pipeline", description="Source pipeline or fast-path trigger")
    reason_codes: List[str] = Field(default_factory=list, description="Machine-readable trigger reason codes")
    status: str = Field("NEW", description="Alert lifecycle status")
    timestamp: str = Field(..., description="ISO timestamp of evaluation")

    model_config = ConfigDict(from_attributes=True)


class CaseRecommendationsResponse(BaseModel):
    """
    Comprehensive clinician decision support response aggregating
    recommendations, tailored self-help resources, and evaluated safety protocol.

    Returned by:
      GET /api/v1/therapist/cases/{case_id}/recommendations
      GET /api/v1/therapist/sessions/{session_id}/recommendations
    """
    case_id: uuid.UUID = Field(..., description="Unique case identifier")
    victim_id: str = Field(..., description="External victim identifier")
    session_id: Optional[uuid.UUID] = Field(None, description="Associated session ID if session-specific")
    timepoint: Optional[int] = Field(None, description="Current or assessed timepoint index")

    # Availability sentinel
    results_available: bool = Field(
        ...,
        description="True if prediction/assessment data is available to generate recommendations, False otherwise."
    )

    # Underlying assessment indicators (read-only decision support)
    risk_level: Optional[str] = Field(None, description="Risk level (LOW, MODERATE, HIGH, CRITICAL, or null)")
    triage_level: Optional[str] = Field(None, description="Triage classification (LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN)")
    fused_risk_score: Optional[float] = Field(None, description="Overall fused DDS risk score (0-100)")

    # Recommendations and resources
    recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Rank-ordered intervention recommendations"
    )
    self_help_resources: List[SelfHelpResourceItem] = Field(
        default_factory=list,
        description="Selected tailored self-help materials"
    )
    safety_protocol: Optional[SafetyProtocolResponse] = Field(
        None,
        description="Current evaluated safety protocol / alert output"
    )

    # Clinical disclaimer
    disclaimer: str = Field(
        "This is a support-oriented recommendation and is not a medical diagnosis.",
        description="Mandatory clinical decision support disclaimer"
    )

    # Audit timestamp
    generated_at: datetime = Field(..., description="Timestamp when recommendations were generated")

    model_config = ConfigDict(from_attributes=True)
