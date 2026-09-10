"""
User Repository
===============

Data access methods for User records.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling CRUD operations for User entities."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Finds a user by unique email address."""
        statement = select(User).where(User.email == email)
        return self.db.scalars(statement).first()

    def get_by_mobile(self, mobile: str) -> Optional[User]:
        """Finds a user by unique mobile number."""
        statement = select(User).where(User.mobile == mobile)
        return self.db.scalars(statement).first()

    def list_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves users filtered by role."""
        statement = (
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_by_status(self, status: UserStatus, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves users filtered by operational status."""
        statement = (
            select(User)
            .where(User.status == status)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
