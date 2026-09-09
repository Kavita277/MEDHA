from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.session import Session as DBSession, Answer
from app.models.patient import Patient
from app.schemas.session_schema import SessionCreate, AnswerCreate
from app.utils.question_engine import get_next_question

def create_session(db: Session, session: SessionCreate):
    patient = db.query(Patient).filter(Patient.patient_id == session.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    db_session = DBSession(session_id=session.session_id, patient_id=session.patient_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: str):
    session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

def submit_answer(db: Session, session_id: str, answer: AnswerCreate):
    session = get_session(db, session_id)
    db_answer = Answer(
        session_id=session_id,
        question_id=answer.question_id,
        answer_data=answer.answer_data
    )
    db.add(db_answer)
    db.commit()
    return {"message": "Answer saved successfully"}

def get_next_question_for_session(db: Session, session_id: str):
    session = get_session(db, session_id)
    answered = [a.question_id for a in session.answers]
    question = get_next_question(answered)
    if not question:
        return {"message": "No more questions"}
    return question
