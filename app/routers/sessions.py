from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.session_schema import SessionCreate, SessionResponse, AnswerCreate
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    return session_service.create_session(db, session)

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    return session_service.get_session(db, session_id)

@router.post("/{session_id}/answer")
def submit_answer(session_id: str, answer: AnswerCreate, db: Session = Depends(get_db)):
    return session_service.submit_answer(db, session_id, answer)

@router.get("/{session_id}/next-question")
def next_question(session_id: str, db: Session = Depends(get_db)):
    return session_service.get_next_question_for_session(db, session_id)
