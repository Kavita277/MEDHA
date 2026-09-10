import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.v1.endpoints.auth import get_current_user
from backend.persistence.database import get_db
from backend.persistence.models.user import User
from backend.services.case_service import CaseService
from backend.services import journal_service
from backend.schemas.journal import (
    JournalEntryCreate, 
    JournalEntryUpdate, 
    JournalEntryResponse, 
    JournalEntryListResponse
)

router = APIRouter()

@router.post("", response_model=JournalEntryResponse)
def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = CaseService(db).get_active_case_for_user(current_user.id)
    new_entry = journal_service.create_entry(db, case.id, entry.content)
    return JournalEntryResponse.model_validate(new_entry)

@router.get("", response_model=JournalEntryListResponse)
def list_journal_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = CaseService(db).get_active_case_for_user(current_user.id)
    entries = journal_service.get_entries(db, case.id)
    return JournalEntryListResponse(entries=[JournalEntryResponse.model_validate(e) for e in entries])

@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = CaseService(db).get_active_case_for_user(current_user.id)
    entry = journal_service.get_entry(db, case.id, entry_id)
    return JournalEntryResponse.model_validate(entry)

@router.patch("/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: uuid.UUID,
    update_data: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = CaseService(db).get_active_case_for_user(current_user.id)
    entry = journal_service.update_entry(db, case.id, entry_id, update_data.content)
    return JournalEntryResponse.model_validate(entry)
