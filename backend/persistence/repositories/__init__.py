"""
MEDHA Repositories Package
==========================

Contains generic and domain-specific data access repositories.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository providing standard CRUD abstraction over SQLAlchemy models.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Retrieves a single record by primary key."""
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieves a paginated list of records."""
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())

    def add(self, obj: ModelType) -> ModelType:
        """Persists a new record."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def create(self, obj: ModelType) -> ModelType:
        """Alias for add to persist a new record."""
        return self.add(obj)


    def delete(self, obj: ModelType) -> None:
        """Deletes a record."""
        self.db.delete(obj)
        self.db.commit()


from backend.persistence.repositories.user import UserRepository
from backend.persistence.repositories.therapist import TherapistRepository
from backend.persistence.repositories.case import CaseRepository
from backend.persistence.repositories.session import SessionRepository
from backend.persistence.repositories.prediction_result import PredictionResultRepository
from backend.persistence.repositories.audit_log import AuditLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "TherapistRepository",
    "CaseRepository",
    "SessionRepository",
    "PredictionResultRepository",
    "AuditLogRepository",
]



