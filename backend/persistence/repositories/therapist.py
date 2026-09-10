"""
Therapist Repository
====================

Data access methods for Therapist profile records.
"""

from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.persistence.models.therapist import Therapist
from backend.persistence.repositories import BaseRepository


class TherapistRepository(BaseRepository[Therapist]):
    """Repository handling CRUD operations for Therapist entities."""

    def __init__(self, db: Session):
        super().__init__(Therapist, db)

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Therapist]:
        """Finds a therapist profile by linked user_id."""
        statement = select(Therapist).where(Therapist.user_id == user_id)
        return self.db.scalars(statement).first()

    def get_with_user(self, therapist_id: uuid.UUID) -> Optional[Therapist]:
        """Retrieves a therapist profile with eager-loaded user account information."""
        statement = (
            select(Therapist)
            .options(joinedload(Therapist.user))
            .where(Therapist.id == therapist_id)
        )
        return self.db.scalars(statement).first()
