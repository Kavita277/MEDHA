"""
Authentication & Authorization Dependencies
===========================================

FastAPI dependency providers for user authentication, token extraction, and RBAC.
"""

from __future__ import annotations

import uuid
from typing import Callable, List, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.repositories.user import UserRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.security.tokens import decode_access_token

# OAuth2 bearer scheme for Swagger UI & Authorization header parsing
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and validates the JWT bearer token, retrieves the corresponding
    User entity, and verifies the account is ACTIVE.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    if not user:
        raise credentials_exception

    # Account status validation
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account access denied. Account status is {user.status.value}.",
        )

    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Dependency factory that enforces the authenticated user possesses one of the allowed roles.
    Raises HTTP 403 Forbidden if unauthorized.
    """
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_names)}.",
            )
        return current_user

    return _role_checker


def get_current_therapist(
    current_user: User = Depends(require_role(UserRole.THERAPIST)),
    db: Session = Depends(get_db),
) -> Therapist:
    """
    Ensures the current user is an authenticated THERAPIST and returns
    their linked Therapist profile record.
    """
    therapist_repo = TherapistRepository(db)
    therapist = therapist_repo.get_by_user_id(current_user.id)
    if not therapist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user does not have an associated therapist profile.",
        )
    return therapist


def get_current_patient(
    current_user: User = Depends(require_role(UserRole.USER)),
) -> User:
    """
    Ensures the current user is an authenticated patient with USER role.
    """
    return current_user
