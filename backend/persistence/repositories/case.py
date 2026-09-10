"""
Case Repository
===============

Data access methods for Case entities and therapist-patient roster lookups.
"""

from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.persistence.models.case import Case
from backend.persistence.models.user import User
from backend.persistence.repositories import BaseRepository


class CaseRepository(BaseRepository[Case]):
    """Repository handling CRUD operations and queries for Case containers."""

    def __init__(self, db: Session):
        super().__init__(Case, db)

    def get_by_victim_id(self, victim_id: str) -> Optional[Case]:
        """Finds a case by the unique external Victim_ID."""
        statement = select(Case).where(Case.victim_id == victim_id)
        return self.db.scalars(statement).first()

    def get_active_case_for_user(self, user_id: uuid.UUID) -> Optional[Case]:
        """Retrieves the currently active case for a patient."""
        statement = (
            select(Case)
            .where(Case.user_id == user_id, Case.status == "active")
        )
        return self.db.scalars(statement).first()

    def list_cases_for_therapist(self, therapist_id: uuid.UUID) -> List[Case]:
        """Lists all cases assigned to a therapist."""
        statement = (
            select(Case)
            .where(Case.therapist_id == therapist_id)
            .order_by(Case.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_users_for_therapist(self, therapist_id: uuid.UUID) -> List[User]:
        """
        Retrieves all patient User records assigned to a specific clinician.
        Guarantees strict data isolation: only users belonging to this therapist are returned.
        """
        statement = (
            select(User)
            .join(Case, Case.user_id == User.id)
            .where(Case.therapist_id == therapist_id)
            .order_by(User.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_therapist_patient(self, therapist_id: uuid.UUID, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieves a single patient if and only if they are assigned to the specified therapist.
        """
        statement = (
            select(User)
            .join(Case, Case.user_id == User.id)
            .where(Case.therapist_id == therapist_id, User.id == user_id)
        )
        return self.db.scalars(statement).first()
