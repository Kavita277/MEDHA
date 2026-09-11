"""
Authentication Endpoints
========================

Provides authentication mechanisms:
- POST /api/v1/auth/login: Authenticates user credentials and returns JWT Bearer token
- GET /api/v1/auth/me: Retrieves the profile of the currently authenticated user
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.dependencies import get_app_settings, get_db
from backend.persistence.models.user import User, UserStatus
from backend.persistence.repositories.user import UserRepository
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.schemas.user import UserResponse
from backend.security.dependencies import get_current_user
from backend.security.passwords import verify_password
from backend.security.tokens import create_access_token
from backend.services.audit_service import audit_service

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates credentials (email & password), validates account status, updates last login, and returns a JWT access token.",
)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    """Authenticates user with email and password."""
    user_repo = UserRepository(db)
    normalized_email = credentials.email.strip().lower()
    user = user_repo.get_by_email(normalized_email)

    if not user or not verify_password(credentials.password, user.password_hash):
        actor_role = user.role.value if (user and hasattr(user.role, "value")) else (str(user.role) if user else None)
        audit_service.log_event(
            db=db,
            action="LOGIN_FAILED",
            actor_user_id=user.id if user else None,
            actor_role=actor_role,
            resource_type="auth",
            resource_id=normalized_email,
            status="FAILURE",
            metadata={"email": normalized_email, "reason": "invalid_credentials"},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        audit_service.log_event(
            db=db,
            action="LOGIN_BLOCKED",
            actor_user_id=user.id,
            actor_role=role_val,
            resource_type="auth",
            resource_id=str(user.id),
            status="DENIED",
            metadata={"email": user.email, "account_status": user.status.value},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account access denied. Account status is {user.status.value}.",
        )

    # Record login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    # Create JWT access token
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    token_payload = {
        "sub": str(user.id),
        "role": role_val,
        "email": user.email,
    }
    access_token = create_access_token(data=token_payload)

    # Record successful login audit event
    audit_service.log_event(
        db=db,
        action="USER_LOGIN",
        actor_user_id=user.id,
        actor_role=role_val,
        resource_type="user",
        resource_id=str(user.id),
        status="SUCCESS",
        metadata={"email": user.email, "role": role_val},
        request=request,
    )
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )



@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns the profile information of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
