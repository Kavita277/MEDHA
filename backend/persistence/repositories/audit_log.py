"""
Audit Log Repository
====================

Data access layer for AuditLogModel records.

Design & Architectural Contract:
  - Application-level append-only repository.
  - Exposes creation and query methods only; no update or deletion methods are provided.
  - Query methods support filtering by actor, action, resource, status, and time range.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.persistence.models.audit_log import AuditLogModel
from backend.persistence.repositories import BaseRepository


class AuditLogRepository(BaseRepository[AuditLogModel]):
    """
    Repository for compliance audit logs.
    Provides application-level append-only access to audit records.
    """

    def __init__(self, db: Session):
        super().__init__(AuditLogModel, db)

    def create_log(
        self,
        action: str,
        actor_user_id: Optional[uuid.UUID] = None,
        actor_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata_payload: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> AuditLogModel:
        """
        Appends a new audit log entry to the database.
        """
        audit_entry = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_payload=metadata_payload,
        )
        if created_at is not None:
            audit_entry.created_at = created_at

        self.db.add(audit_entry)
        self.db.flush()
        return audit_entry

    def list_logs(
        self,
        actor_user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogModel]:
        """
        Queries audit logs with optional filtering, ordered newest first.
        """
        stmt = select(AuditLogModel)

        if actor_user_id is not None:
            stmt = stmt.where(AuditLogModel.actor_user_id == actor_user_id)
        if action is not None:
            stmt = stmt.where(AuditLogModel.action == action)
        if resource_type is not None:
            stmt = stmt.where(AuditLogModel.resource_type == resource_type)
        if resource_id is not None:
            stmt = stmt.where(AuditLogModel.resource_id == resource_id)
        if status is not None:
            stmt = stmt.where(AuditLogModel.status == status)
        if start_time is not None:
            stmt = stmt.where(AuditLogModel.created_at >= start_time)
        if end_time is not None:
            stmt = stmt.where(AuditLogModel.created_at <= end_time)

        stmt = stmt.order_by(AuditLogModel.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_logs(
        self,
        actor_user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Counts total matching audit records.
        """
        stmt = select(func.count(AuditLogModel.id))

        if actor_user_id is not None:
            stmt = stmt.where(AuditLogModel.actor_user_id == actor_user_id)
        if action is not None:
            stmt = stmt.where(AuditLogModel.action == action)
        if resource_type is not None:
            stmt = stmt.where(AuditLogModel.resource_type == resource_type)
        if resource_id is not None:
            stmt = stmt.where(AuditLogModel.resource_id == resource_id)
        if status is not None:
            stmt = stmt.where(AuditLogModel.status == status)

        count_val = self.db.scalar(stmt)
        return count_val or 0
