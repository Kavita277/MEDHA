"""
Event Repository
================

Data access layer for behavior telemetry events.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.persistence.models.event import RawEventModel


class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def batch_insert_idempotent(self, events: List[RawEventModel]) -> int:
        """
        Inserts a batch of events idempotently by ignoring duplicate event_ids.
        Returns the number of successfully inserted events.
        """
        inserted_count = 0
        for event in events:
            # We attempt to insert each event individually to gracefully handle IntegrityError
            # on duplicate event_id without failing the entire batch.
            # In a production PostgreSQL environment, we would use INSERT ... ON CONFLICT DO NOTHING
            # for bulk performance. Since we must support SQLite for testing, we use nested transactions.
            try:
                with self.session.begin_nested():
                    self.session.add(event)
                inserted_count += 1
            except IntegrityError:
                # event_id unique constraint violated; safely ignore the duplicate
                pass
                
        self.session.flush()
        return inserted_count
