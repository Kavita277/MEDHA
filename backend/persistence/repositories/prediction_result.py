"""
Prediction Result Repository
=============================

Data access layer for PredictionResultModel records.

Authorization note:
  This repository performs NO authorization checks. Authorization must be
  enforced by the calling service/endpoint layer (therapist case ownership
  must be verified BEFORE calling these methods).
"""

from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.repositories import BaseRepository


class PredictionResultRepository(BaseRepository[PredictionResultModel]):
    """Repository for CRUD operations on PredictionResultModel."""

    def __init__(self, db: Session):
        super().__init__(PredictionResultModel, db)

    def get_latest_for_case(self, case_id: uuid.UUID) -> Optional[PredictionResultModel]:
        """
        Returns the most recent prediction for a given case (ordered by predicted_at DESC).
        Returns None if no prediction records exist for this case.
        """
        stmt = (
            select(PredictionResultModel)
            .where(PredictionResultModel.case_id == case_id)
            .order_by(PredictionResultModel.predicted_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_latest_for_session(self, session_id: uuid.UUID) -> Optional[PredictionResultModel]:
        """
        Returns the most recent prediction associated with a given session.
        Returns None if no prediction records exist for this session.
        """
        stmt = (
            select(PredictionResultModel)
            .where(PredictionResultModel.session_id == session_id)
            .order_by(PredictionResultModel.predicted_at.desc())
        )
        return self.db.scalars(stmt).first()

    def list_for_case(self, case_id: uuid.UUID) -> List[PredictionResultModel]:
        """
        Returns all predictions for a case, ordered most recent first.
        """
        stmt = (
            select(PredictionResultModel)
            .where(PredictionResultModel.case_id == case_id)
            .order_by(PredictionResultModel.predicted_at.desc())
        )
        return list(self.db.scalars(stmt).all())
