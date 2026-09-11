"""
Audit Log Schemas
=================

Pydantic validation and response schemas for compliance and security audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """
    Structured response model for an audit log entry.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique audit record identifier")
    actor_user_id: Optional[uuid.UUID] = Field(None, description="User ID of the actor (if authenticated)")
    actor_role: Optional[str] = Field(None, description="Role of the actor at the time of the event")
    action: str = Field(..., description="Action name / security event type")
    resource_type: Optional[str] = Field(None, description="Type of target resource")
    resource_id: Optional[str] = Field(None, description="Identifier of target resource")
    status: str = Field(..., description="Event status: SUCCESS, FAILURE, DENIED, ERROR")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    metadata_payload: Optional[Dict[str, Any]] = Field(None, description="Redacted metadata payload")
    created_at: datetime = Field(..., description="Timestamp of the audit event")


class AuditLogListResponse(BaseModel):
    """
    Paginated list response for audit log queries.
    """
    total: int = Field(..., description="Total count of matching audit logs")
    items: List[AuditLogResponse] = Field(default_factory=list, description="List of audit logs")
