"""
Check-In Repository
===================

Data access layer for CheckIns and QuestionRecords.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel, CheckInStatus


class CheckInRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_checkin(self, checkin: CheckInModel) -> CheckInModel:
        self.session.add(checkin)
        self.session.flush()
        return checkin

    def get_checkin_by_id(self, checkin_id: uuid.UUID) -> Optional[CheckInModel]:
        stmt = (
            select(CheckInModel)
            .options(joinedload(CheckInModel.questions))
            .where(CheckInModel.id == checkin_id)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_active_checkin_for_session(self, session_id: uuid.UUID) -> Optional[CheckInModel]:
        stmt = (
            select(CheckInModel)
            .options(joinedload(CheckInModel.questions))
            .where(
                CheckInModel.session_id == session_id,
                CheckInModel.status.in_([CheckInStatus.PENDING.value, CheckInStatus.IN_PROGRESS.value])
            )
            .order_by(CheckInModel.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def create_question_record(self, record: QuestionRecordModel) -> QuestionRecordModel:
        self.session.add(record)
        self.session.flush()
        return record

    def get_question_record_by_id(self, record_id: uuid.UUID) -> Optional[QuestionRecordModel]:
        stmt = select(QuestionRecordModel).where(QuestionRecordModel.id == record_id)
        return self.session.execute(stmt).scalar_one_or_none()
