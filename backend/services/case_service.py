"""
Case Service
============

Domain business logic for managing cases and verifying clinician/patient ownership.
"""

from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.persistence.models.case import Case
from backend.persistence.models.user import User, UserRole
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.therapist import TherapistRepository


class CaseService:
    """Business operations for Case management and role-based access validation."""

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.therapist_repo = TherapistRepository(db)

    def get_case(self, case_id: uuid.UUID) -> Optional[Case]:
        """Retrieves case by UUID."""
        return self.case_repo.get(case_id)

    def get_case_by_victim_id(self, victim_id: str) -> Optional[Case]:
        """Retrieves case by unique external Victim_ID."""
        return self.case_repo.get_by_victim_id(victim_id)

    def get_active_case_for_user(self, user_id: uuid.UUID) -> Optional[Case]:
        """Retrieves the active case for a patient."""
        return self.case_repo.get_active_case_for_user(user_id)

    def list_cases_for_therapist(self, therapist_id: uuid.UUID) -> List[Case]:
        """Retrieves all cases assigned to a therapist."""
        return self.case_repo.list_cases_for_therapist(therapist_id)

    def verify_case_access(self, user: User, case: Case) -> bool:
        """
        Enforces access control rules:
        - A USER may only access their own case.
        - A THERAPIST may only access cases assigned to them.
        """
        if user.role == UserRole.USER:
            return case.user_id == user.id

        if user.role == UserRole.THERAPIST:
            therapist = self.therapist_repo.get_by_user_id(user.id)
            if not therapist:
                return False
            return case.therapist_id == therapist.id

        return False
