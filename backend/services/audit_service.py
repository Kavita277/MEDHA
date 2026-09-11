"""
Audit Service
=============

Handles security and compliance audit logging for the MEDHA platform.

Key Capabilities:
  - Application-level append-only compliance logging.
  - Strict Privacy & Redaction Firewalls: strips passwords, bcrypt hashes, JWT tokens,
    session secrets, authorization headers, raw voice/audio payloads, and full chat transcripts.
  - Non-blocking persistence: writes to the transactional database session. In the event
    of an unexpected database logging exception, records a structured system error log
    without disrupting clinical workflows unless critical.
  - Structured extraction of client metadata (IP address, User-Agent) from FastAPI requests.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
from fastapi import Request
from sqlalchemy.orm import Session

from backend.persistence.models.audit_log import AuditLogModel
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.security.redaction import sanitize_payload

logger = logging.getLogger(__name__)



class AuditService:
    """
    Centralized service for logging compliance and security events.
    """

    @staticmethod
    def extract_client_info(request: Optional[Request]) -> Dict[str, Optional[str]]:
        """
        Extracts client IP and User-Agent from a FastAPI Request if present.
        """
        if request is None:
            return {"ip_address": None, "user_agent": None}

        # Handle X-Forwarded-For if behind a reverse proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        else:
            ip_address = None

        user_agent = request.headers.get("user-agent")
        return {"ip_address": ip_address, "user_agent": user_agent}

    def log_event(
        self,
        db: Session,
        action: str,
        actor_user_id: Optional[uuid.UUID] = None,
        actor_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[AuditLogModel]:
        """
        Records an audit event into the database with sanitized metadata.

        Architecture & Failure Lifecycle:
          - Automatically sanitizes the metadata payload against sensitive keys.
          - Appends the entry to the provided database session and flushes.
          - If a database exception occurs, the error is caught, logged with high
            severity to the logging subsystem, and does not crash the caller.
        """
        client_info = self.extract_client_info(request)
        final_ip = ip_address or client_info.get("ip_address")
        final_ua = user_agent or client_info.get("user_agent")

        sanitized_meta = sanitize_payload(metadata) if metadata is not None else None

        try:
            repo = AuditLogRepository(db)
            audit_entry = repo.create_log(
                action=action,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                ip_address=final_ip,
                user_agent=final_ua,
                metadata_payload=sanitized_meta,
            )
            return audit_entry
        except Exception as exc:
            logger.error(
                "Failed to persist audit log entry: action=%s actor=%s resource=%s:%s error=%s",
                action,
                actor_user_id,
                resource_type,
                resource_id,
                exc,
                exc_info=True,
            )
            return None


audit_service = AuditService()
