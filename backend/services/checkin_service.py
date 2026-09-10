import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel, CheckInStatus
from backend.persistence.models.session import SessionStatus
from backend.persistence.models.user import User
from backend.persistence.models.event import RawEventModel
from backend.persistence.repositories.checkin import CheckInRepository
from backend.persistence.repositories.event import EventRepository
from backend.services.session_service import SessionService
from chatbot.engines.question_engine import DeterministicQuestionEngine
from backend.integrations.session_state_adapter import restore_medha_state, create_initial_medha_state
from backend.schemas.checkin import CheckInResponse, QuestionResponse, CheckInAnswerResponse

logger = logging.getLogger(__name__)


# Mapping from question ID to Medha V2 Structured Feature
QUESTION_TO_FEATURE_MAP = {
    "SA-01": "Safety",
    "SA-02": "Safety",
    "SA-03": "Safety",
    "SA-04": "Safety",
    "ES-01": "Stress",
    "ES-02": "Stress",
    "ES-03": "Stress",
    "ES-06": "Stress",
    "SF-01": "Sleep",
    "SF-02": "Functioning",
    "SF-03": "Functioning",
    "SF-05": "Functioning",
    "SE-01": "Social_Support_Checkin",
    "SE-02": "Social_Support_Checkin",
    "SE-03": "Social_Support_Checkin",
    "SE-06": "Social_Support_Checkin",
    "GW-01": "Self_Reported_Wellbeing",
    "GW-03": "Self_Reported_Wellbeing",
    "GW-05": "Self_Reported_Wellbeing",
    "GW-06": "Self_Reported_Wellbeing",
}

_MEDHA_EVENTS_NS = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d")

def _deterministic_uuid(ns: uuid.UUID, session_id: str, turn_identifier: str, event_type: str) -> str:
    name = f"{session_id}:{turn_identifier}:{event_type}"
    return str(uuid.uuid5(ns, name))


class CheckInService:
    def __init__(self, db: DBSession):
        self.db = db
        self.checkin_repo = CheckInRepository(db)
        self.session_service = SessionService(db)
        self.event_repo = EventRepository(db)
        self.question_engine = DeterministicQuestionEngine()

    def _verify_session_access(self, session_id: uuid.UUID, current_user: User):
        session_obj = self.session_service.get_session_with_ownership_check(session_id, current_user)
        if session_obj.status != SessionStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Session is not active")
        return session_obj

    def start_checkin(self, session_id: uuid.UUID, current_user: User) -> CheckInResponse:
        session_obj = self._verify_session_access(session_id, current_user)
        
        # Check if already active
        existing_checkin = self.checkin_repo.get_active_checkin_for_session(session_id)
        if existing_checkin:
            return CheckInResponse.model_validate(existing_checkin)

        # Restore State
        if session_obj.state_snapshot:
            medha_state = restore_medha_state(session_obj.state_snapshot)
        else:
            medha_state = create_initial_medha_state(
                victim_id=session_obj.case.victim_id if session_obj.case else "UNKNOWN",
                session_id=session_obj.session_identifier,
                timepoint=session_obj.timepoint,
            )
        
        # Get next question
        next_q_record = self.question_engine.select_next_question(medha_state)
        if not next_q_record:
            raise HTTPException(status_code=400, detail="No check-in needed at this time.")
            
        now = datetime.now(timezone.utc)
        
        checkin = CheckInModel(
            session_id=session_id,
            victim_id=session_obj.case.victim_id,
            status=CheckInStatus.IN_PROGRESS.value,
            started_at=now,
            current_question_id=next_q_record.question_id,
        )
        checkin = self.checkin_repo.create_checkin(checkin)
        
        q_db_record = QuestionRecordModel(
            checkin_id=checkin.id,
            question_id=next_q_record.question_id,
            question_text=next_q_record.question_text,
            question_order=1,
            answer_status="pending",
        )
        self.checkin_repo.create_question_record(q_db_record)
        
        # Emit events
        evt_start = RawEventModel(
            event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_id), "start", "checkin_started"),
            case_id=session_obj.case_id,
            session_id=session_id,
            event_type="checkin_started",
            occurred_at=now,
            metadata_payload={}
        )
        evt_prompt = RawEventModel(
            event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_id), next_q_record.question_id, "checkin_prompt_shown"),
            case_id=session_obj.case_id,
            session_id=session_id,
            event_type="checkin_prompt_shown",
            occurred_at=now,
            metadata_payload={"question_id": next_q_record.question_id}
        )
        self.event_repo.batch_insert_idempotent([evt_start, evt_prompt])
        
        # Update MedhaState with the asked question
        medha_state.record_question_asked(
            question_id=next_q_record.question_id,
            question_text=next_q_record.question_text,
            intent=next_q_record.intent,
            cooldown_until=next_q_record.cooldown_until
        )
        session_obj.state_snapshot = medha_state.to_dict()
        self.db.commit()
        
        self.db.refresh(checkin)
        return CheckInResponse.model_validate(checkin)

    def get_checkin(self, checkin_id: uuid.UUID, current_user: User) -> CheckInResponse:
        checkin = self.checkin_repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
            
        self._verify_session_access(checkin.session_id, current_user)
        return CheckInResponse.model_validate(checkin)

    def submit_answer(
        self, checkin_id: uuid.UUID, current_user: User, answer_data: Dict[str, Any]
    ) -> CheckInAnswerResponse:
        checkin = self.checkin_repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        if checkin.status == CheckInStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Check-in already completed")
            
        session_obj = self._verify_session_access(checkin.session_id, current_user)
        
        # Find active question record
        current_q_record = None
        for q in checkin.questions:
            if q.question_id == checkin.current_question_id and q.answer_status == "pending":
                current_q_record = q
                break
                
        if not current_q_record:
            raise HTTPException(status_code=400, detail="No active question to answer")
            
        # Parse answer
        answer_val = None
        if answer_data:
            # We take the first value from the dict as the semantic value
            values = list(answer_data.values())
            if values:
                answer_val = values[0]
                
        now = datetime.now(timezone.utc)
        
        # Persist answer
        current_q_record.answer = answer_data
        current_q_record.answered_at = now
        current_q_record.answer_status = "answered"
        
        # Update MedhaState
        if session_obj.state_snapshot:
            medha_state = restore_medha_state(session_obj.state_snapshot)
        else:
            medha_state = create_initial_medha_state(
                victim_id=session_obj.case.victim_id if session_obj.case else "UNKNOWN",
                session_id=session_obj.session_identifier,
                timepoint=session_obj.timepoint,
            )
        medha_state.record_question_answered(
            question_id=current_q_record.question_id,
            response_text=json.dumps(answer_data)
        )
        
        feature_name = QUESTION_TO_FEATURE_MAP.get(current_q_record.question_id)
        if feature_name and answer_val is not None:
            try:
                if isinstance(answer_val, bool):
                    answer_val = 1.0 if answer_val else 0.0
                elif isinstance(answer_val, str) and answer_val.isdigit():
                    answer_val = int(answer_val)
                    
                medha_state.update_feature("structured", feature_name, answer_val)
            except Exception as e:
                logger.error(f"Failed to update feature {feature_name} with {answer_val}: {e}")

        events_to_insert = []
        evt_answered = RawEventModel(
            event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), current_q_record.question_id, "checkin_answered"),
            case_id=session_obj.case_id,
            session_id=session_obj.id,
            event_type="checkin_answered",
            occurred_at=now,
            metadata_payload={"question_id": current_q_record.question_id}
        )
        events_to_insert.append(evt_answered)

        # Determine next question
        next_q_record = self.question_engine.select_next_question(medha_state)
        
        if next_q_record:
            checkin.current_question_id = next_q_record.question_id
            new_q_db = QuestionRecordModel(
                checkin_id=checkin.id,
                question_id=next_q_record.question_id,
                question_text=next_q_record.question_text,
                question_order=current_q_record.question_order + 1,
                answer_status="pending",
            )
            self.checkin_repo.create_question_record(new_q_db)
            
            medha_state.record_question_asked(
                question_id=next_q_record.question_id,
                question_text=next_q_record.question_text,
                intent=next_q_record.intent,
                cooldown_until=next_q_record.cooldown_until
            )
            
            evt_prompt = RawEventModel(
                event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), next_q_record.question_id, "checkin_prompt_shown"),
                case_id=session_obj.case_id,
                session_id=session_obj.id,
                event_type="checkin_prompt_shown",
                occurred_at=now,
                metadata_payload={"question_id": next_q_record.question_id}
            )
            events_to_insert.append(evt_prompt)
        else:
            checkin.status = CheckInStatus.COMPLETED.value
            checkin.completed_at = now
            checkin.current_question_id = None
            
            evt_completed = RawEventModel(
                event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), "complete_auto", "checkin_completed"),
                case_id=session_obj.case_id,
                session_id=session_obj.id,
                event_type="checkin_completed",
                occurred_at=now,
                metadata_payload={"method": "auto"}
            )
            events_to_insert.append(evt_completed)
            
        self.event_repo.batch_insert_idempotent(events_to_insert)
            
        session_obj.state_snapshot = medha_state.to_dict()
        self.db.commit()
        self.db.refresh(checkin)
        
        next_q_resp = None
        if checkin.current_question_id:
            for q in checkin.questions:
                if q.question_id == checkin.current_question_id:
                    next_q_resp = QuestionResponse.model_validate(q)
                    break

        return CheckInAnswerResponse(
            status=checkin.status,
            checkin=CheckInResponse.model_validate(checkin),
            next_question=next_q_resp
        )

    def complete_checkin(self, checkin_id: uuid.UUID, current_user: User) -> CheckInResponse:
        checkin = self.checkin_repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        
        session_obj = self._verify_session_access(checkin.session_id, current_user)
        
        if checkin.status == CheckInStatus.COMPLETED.value:
            return CheckInResponse.model_validate(checkin)

        now = datetime.now(timezone.utc)
        checkin.status = CheckInStatus.COMPLETED.value
        checkin.completed_at = now
        checkin.current_question_id = None
        
        evt_completed = RawEventModel(
            event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), "complete_manual", "checkin_completed"),
            case_id=session_obj.case_id,
            session_id=session_obj.id,
            event_type="checkin_completed",
            occurred_at=now,
            metadata_payload={"method": "manual"}
        )
        self.event_repo.batch_insert_idempotent([evt_completed])
        
        self.db.commit()
        self.db.refresh(checkin)
        
        return CheckInResponse.model_validate(checkin)
