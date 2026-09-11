"""
Therapist Management Endpoints
==============================

Provides clinician-facing endpoints:
- POST /api/v1/therapist/users: Creates a new patient account and associated case
- GET /api/v1/therapist/users: Lists patient accounts assigned to the authenticated therapist
"""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.case import Case
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.user import UserRepository
from backend.persistence.repositories.audit_log import AuditLogRepository
from backend.schemas.case import (
    CaseResponse,
    TherapistCreateUserRequest,
    TherapistUserResponse,
)
from backend.schemas.audit import AuditLogResponse
from backend.security.dependencies import get_current_therapist
from backend.security.passwords import hash_password
from backend.services.audit_service import audit_service

router = APIRouter()



@router.post(
    "/users",
    response_model=TherapistUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Patient Account and Case",
    description="Allows an authenticated therapist to provision a new patient account with a securely hashed password and an assigned case.",
)
def create_patient_user(
    payload: TherapistCreateUserRequest,
    request: Request,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> TherapistUserResponse:
    """Creates a patient account and connects them via a Case record to the therapist."""
    user_repo = UserRepository(db)
    case_repo = CaseRepository(db)

    # 1. Validate email uniqueness
    normalized_email = payload.email.strip().lower()
    if user_repo.get_by_email(normalized_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # 2. Validate mobile uniqueness if provided
    if payload.mobile and user_repo.get_by_mobile(payload.mobile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists.",
        )

    # 3. Determine and validate victim_id
    victim_id = payload.victim_id.strip() if payload.victim_id else f"V-{uuid.uuid4().hex[:8].upper()}"
    if case_repo.get_by_victim_id(victim_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A case with Victim ID '{victim_id}' already exists.",
        )

    # 4. Hash password securely
    hashed = hash_password(payload.password)

    # 5. Create user record
    new_user = User(
        id=uuid.uuid4(),
        role=UserRole.USER,
        name=payload.name.strip(),
        mobile=payload.mobile.strip() if payload.mobile else None,
        email=normalized_email,
        password_hash=hashed,
        status=UserStatus.ACTIVE,
        must_change_password=True,
    )
    user_repo.create(new_user)

    # 6. Create linked case record
    new_case = Case(
        id=uuid.uuid4(),
        victim_id=victim_id,
        user_id=new_user.id,
        therapist_id=current_therapist.id,
        current_timepoint=1,
        status="active",
    )
    case_repo.create(new_case)

    # 7. Audit log patient provisioning
    audit_service.log_event(
        db=db,
        action="THERAPIST_CREATED_USER",
        actor_user_id=current_therapist.user_id,
        actor_role="therapist",
        resource_type="user",
        resource_id=str(new_user.id),
        status="SUCCESS",
        metadata={
            "patient_email": normalized_email,
            "victim_id": victim_id,
            "case_id": str(new_case.id),
        },
        request=request,
    )

    db.commit()
    db.refresh(new_user)
    db.refresh(new_case)


    return TherapistUserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        mobile=new_user.mobile,
        role=new_user.role,
        status=new_user.status,
        must_change_password=new_user.must_change_password,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login_at=new_user.last_login_at,
        case=CaseResponse.model_validate(new_case),
    )


@router.get(
    "/users",
    response_model=List[TherapistUserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Assigned Patients",
    description="Returns all patient users assigned to the authenticated therapist. Strict isolation: cannot see patients of other therapists.",
)
def list_patient_users(
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[TherapistUserResponse]:
    """Lists patients assigned to the authenticated therapist with case metadata."""
    stmt = (
        select(Case, User)
        .join(User, Case.user_id == User.id)
        .where(Case.therapist_id == current_therapist.id)
        .order_by(User.name.asc())
    )
    rows = db.execute(stmt).all()

    results: List[TherapistUserResponse] = []
    for case, user in rows:
        results.append(
            TherapistUserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                mobile=user.mobile,
                role=user.role,
                status=user.status,
                must_change_password=user.must_change_password,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at,
                case=CaseResponse.model_validate(case),
            )
        )
    return results


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="List Therapist Audit Logs",
    description="Returns compliance audit logs initiated by the authenticated therapist. Strict isolation: cannot see actions of other actors.",
)
def list_therapist_audit_logs(
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_therapist: Therapist = Depends(get_current_therapist),
    db: Session = Depends(get_db),
) -> List[AuditLogResponse]:
    """Returns audit logs for the authenticated therapist."""
    repo = AuditLogRepository(db)
    logs = repo.list_logs(
        actor_user_id=current_therapist.user_id,
        action=action,
        limit=min(limit, 100),
        offset=offset,
    )
    return [AuditLogResponse.model_validate(log) for log in logs]

