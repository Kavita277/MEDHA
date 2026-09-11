"""
Case History & Clinical Event Schemas
======================================

Pydantic schemas for clinician-managed patient case history,
clinical intake profile, and chronological clinical events.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Case History Schemas
# ---------------------------------------------------------------------------

class CaseHistoryUpsertRequest(BaseModel):
    """Payload to create or update a patient's case history profile."""
    # Demographics & Intake
    date_of_birth: Optional[str] = Field(None, max_length=32, description="YYYY-MM-DD or readable DOB")
    age: Optional[int] = Field(None, ge=0, le=130, description="Current age in years")
    gender: Optional[str] = Field(None, max_length=64, description="Gender identity")
    pronouns: Optional[str] = Field(None, max_length=32, description="Preferred pronouns")
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=32)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=64)

    # Clinical Background
    primary_diagnosis: Optional[str] = Field(None, max_length=255, description="Primary diagnostic impression")
    secondary_diagnosis: Optional[str] = Field(None, max_length=255, description="Secondary or comorbid conditions")
    psychiatric_history: Optional[str] = Field(None, description="Past psychiatric treatment, hospitalizations, therapy")
    medical_history: Optional[str] = Field(None, description="General medical conditions, surgeries, chronic illnesses")
    current_medications: Optional[str] = Field(None, description="Prescriptions, dosages, and compliance notes")
    allergies: Optional[str] = Field(None, description="Drug or environmental allergies")
    family_mental_health_history: Optional[str] = Field(None, description="Family psychiatric history")
    substance_use_history: Optional[str] = Field(None, description="Alcohol, nicotine, or substance history")
    trauma_or_stressors: Optional[str] = Field(None, description="Key stressors, adverse life events, trauma background")
    risk_factors: Optional[str] = Field(None, description="Self-harm, suicide risk history, or safety considerations")
    treatment_goals: Optional[str] = Field(None, description="Agreed therapeutic goals and care plan targets")
    clinical_notes: Optional[str] = Field(None, description="Therapist intake notes and clinical observations")


class CaseHistoryResponse(BaseModel):
    """Full serialized representation of a patient case history profile."""
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    therapist_id: uuid.UUID

    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    primary_diagnosis: Optional[str] = None
    secondary_diagnosis: Optional[str] = None
    psychiatric_history: Optional[str] = None
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    allergies: Optional[str] = None
    family_mental_health_history: Optional[str] = None
    substance_use_history: Optional[str] = None
    trauma_or_stressors: Optional[str] = None
    risk_factors: Optional[str] = None
    treatment_goals: Optional[str] = None
    clinical_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Clinical Event Schemas
# ---------------------------------------------------------------------------

class ClinicalEventCreateRequest(BaseModel):
    """Payload to log a new clinical event or milestone."""
    title: str = Field(..., min_length=1, max_length=255, description="Brief summary headline")
    event_type: str = Field(
        default="SESSION_NOTE",
        max_length=64,
        description="Category: SESSION_NOTE, MEDICATION_CHANGE, PANIC_ATTACK, CRISIS_INCIDENT, LIFE_STRESSOR, HOSPITAL_VISIT, MILESTONE, OTHER",
    )
    severity: str = Field(
        default="MEDIUM",
        max_length=32,
        description="Rating: LOW, MEDIUM, HIGH, CRITICAL",
    )
    occurred_at: Optional[datetime] = Field(
        None,
        description="Timestamp when event occurred (defaults to now)",
    )
    description: str = Field(..., min_length=1, description="Clinical notes and narrative context")
    action_taken: Optional[str] = Field(None, description="Intervention applied, advice given, or next steps")
    metadata_payload: Optional[Dict[str, Any]] = Field(None, description="Structured clinical parameters")


class ClinicalEventUpdateRequest(BaseModel):
    """Payload to update an existing clinical event."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    event_type: Optional[str] = Field(None, max_length=64)
    severity: Optional[str] = Field(None, max_length=32)
    occurred_at: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=1)
    action_taken: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class ClinicalEventResponse(BaseModel):
    """Serialized representation of a clinical event."""
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    therapist_id: uuid.UUID

    title: str
    event_type: str
    severity: str
    occurred_at: datetime
    description: str
    action_taken: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
