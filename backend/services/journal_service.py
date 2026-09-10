import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.case import Case

def create_entry(db: Session, case_id: uuid.UUID, content: str) -> JournalEntryModel:
    entry = JournalEntryModel(case_id=case_id, content=content)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_entries(db: Session, case_id: uuid.UUID) -> List[JournalEntryModel]:
    return db.query(JournalEntryModel).filter(JournalEntryModel.case_id == case_id).all()

def get_entry(db: Session, case_id: uuid.UUID, entry_id: uuid.UUID) -> JournalEntryModel:
    entry = db.query(JournalEntryModel).filter(
        JournalEntryModel.case_id == case_id,
        JournalEntryModel.id == entry_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry

def update_entry(db: Session, case_id: uuid.UUID, entry_id: uuid.UUID, content: str) -> JournalEntryModel:
    entry = get_entry(db, case_id, entry_id)
    entry.content = content
    db.commit()
    db.refresh(entry)
    return entry
