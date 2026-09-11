import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
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

def _normalize_answer_to_numeric(question_id: str, val: Any) -> float:
    if val is None:
        return 3.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, bool):
        if question_id == "SA-02":
            return 1.0 if val else 5.0
        if question_id in ("ES-01", "ES-06"):
            return 4.5 if val else 1.5
        return 5.0 if val else 1.0
    if isinstance(val, str):
        v = val.strip().lower()
        if question_id == "SA-02":
            if v in ("yes", "true", "i feel unsafe", "threatened"):
                return 1.0
            return 5.0
        if question_id in ("ES-01", "ES-06"):
            if v in ("yes", "true"):
                return 4.5
            return 1.5
        if v in ("1", "1.0", "low", "1 - low", "not at all", "none", "never", "worse"):
            return 1.0
        if v in ("2", "2.0", "mild", "2 - mild", "rarely"):
            return 2.0
        if v in ("3", "3.0", "moderate", "3 - moderate", "partially", "some, not all", "sometimes", "same", "about the same", "prefer not to say"):
            return 3.0
        if v in ("4", "4.0", "good", "4 - good", "mostly", "often", "better"):
            return 4.0
        if v in ("5", "5.0", "high", "5 - high", "fully", "all of them", "very often", "great"):
            return 5.0
        if v in ("yes", "true"):
            return 5.0
        if v in ("no", "false"):
            return 1.0
        try:
            return float(v)
        except ValueError:
            return 3.0
    return 3.0


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
            enriched_questions = [self._build_question_response(q) for q in existing_checkin.questions]
            return CheckInResponse(
                id=existing_checkin.id,
                session_id=existing_checkin.session_id,
                status=existing_checkin.status,
                started_at=existing_checkin.started_at,
                completed_at=existing_checkin.completed_at,
                current_question_id=existing_checkin.current_question_id,
                questions=enriched_questions,
            )

        # Restore State
        if session_obj.state_snapshot:
            medha_state = restore_medha_state(session_obj.state_snapshot)
        else:
            medha_state = create_initial_medha_state(
                victim_id=session_obj.case.victim_id if session_obj.case else "UNKNOWN",
                session_id=session_obj.session_identifier,
                timepoint=session_obj.timepoint,
            )
        
        # Select randomized 10-15 questions across domains
        selected_qs = self.question_engine.select_random_checkin_questions(state=medha_state)
        if not selected_qs:
            next_q_record = self.question_engine.select_next_question(medha_state)
            if not next_q_record:
                raise HTTPException(status_code=400, detail="No check-in needed at this time.")
            selected_qs = [{
                "question_id": next_q_record.question_id,
                "question": next_q_record.question_text,
                "intent": next_q_record.intent,
                "cooldown_days": 1,
            }]
            
        now = datetime.now(timezone.utc)
        first_q = selected_qs[0]
        
        checkin = CheckInModel(
            session_id=session_id,
            victim_id=session_obj.case.victim_id,
            status=CheckInStatus.IN_PROGRESS.value,
            started_at=now,
            current_question_id=first_q["question_id"],
        )
        checkin = self.checkin_repo.create_checkin(checkin)
        
        for idx, q_dict in enumerate(selected_qs, start=1):
            q_db_record = QuestionRecordModel(
                checkin_id=checkin.id,
                question_id=q_dict["question_id"],
                question_text=q_dict["question"],
                question_order=idx,
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
            metadata_payload={"total_questions": len(selected_qs)}
        )
        evt_prompt = RawEventModel(
            event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_id), first_q["question_id"], "checkin_prompt_shown"),
            case_id=session_obj.case_id,
            session_id=session_id,
            event_type="checkin_prompt_shown",
            occurred_at=now,
            metadata_payload={"question_id": first_q["question_id"]}
        )
        self.event_repo.batch_insert_idempotent([evt_start, evt_prompt])
        
        # Update MedhaState with the first asked question
        medha_state.record_question_asked(
            question_id=first_q["question_id"],
            question_text=first_q["question"],
            intent=first_q.get("intent", "checkin"),
            cooldown_until=(now + timedelta(days=first_q.get("cooldown_days", 1))).isoformat()
        )
        session_obj.state_snapshot = medha_state.to_dict()
        self.db.commit()
        
        self.db.refresh(checkin)
        enriched_questions = [self._build_question_response(q) for q in checkin.questions]
        return CheckInResponse(
            id=checkin.id,
            session_id=checkin.session_id,
            status=checkin.status,
            started_at=checkin.started_at,
            completed_at=checkin.completed_at,
            current_question_id=checkin.current_question_id,
            questions=enriched_questions,
        )

    def get_checkin(self, checkin_id: uuid.UUID, current_user: User) -> CheckInResponse:
        checkin = self.checkin_repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
            
        self._verify_session_access(checkin.session_id, current_user)
        enriched_questions = [self._build_question_response(q) for q in checkin.questions]
        return CheckInResponse(
            id=checkin.id,
            session_id=checkin.session_id,
            status=checkin.status,
            started_at=checkin.started_at,
            completed_at=checkin.completed_at,
            current_question_id=checkin.current_question_id,
            questions=enriched_questions,
        )

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
        if feature_name:
            try:
                numeric_val = _normalize_answer_to_numeric(current_q_record.question_id, answer_val)
                medha_state.update_feature("structured", feature_name, numeric_val)
                if feature_name == "Self_Reported_Wellbeing":
                    medha_state.update_feature("structured", "Mood", numeric_val)
            except Exception as e:
                logger.error(f"Failed to update feature {feature_name} with {answer_val}: {e}")

        # Always set Checkin_Available upon answering
        medha_state.update_feature("structured", "Checkin_Available", 1.0)

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

        # Look for next pending question in checkin.questions
        next_pending_q = None
        for q in sorted(checkin.questions, key=lambda x: x.question_order):
            if q.answer_status == "pending" and q.id != current_q_record.id:
                next_pending_q = q
                break

        if next_pending_q:
            checkin.current_question_id = next_pending_q.question_id
            medha_state.record_question_asked(
                question_id=next_pending_q.question_id,
                question_text=next_pending_q.question_text,
                intent="checkin_question",
                cooldown_until=None,
            )
            evt_prompt = RawEventModel(
                event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), next_pending_q.question_id, "checkin_prompt_shown"),
                case_id=session_obj.case_id,
                session_id=session_obj.id,
                event_type="checkin_prompt_shown",
                occurred_at=now,
                metadata_payload={"question_id": next_pending_q.question_id}
            )
            events_to_insert.append(evt_prompt)
        else:
            checkin.status = CheckInStatus.COMPLETED.value
            checkin.completed_at = now
            checkin.current_question_id = None
            
            evt_completed = RawEventModel(
                event_id=_deterministic_uuid(_MEDHA_EVENTS_NS, str(session_obj.id), "complete_all_answered", "checkin_completed"),
                case_id=session_obj.case_id,
                session_id=session_obj.id,
                event_type="checkin_completed",
                occurred_at=now,
                metadata_payload={"method": "all_answered"}
            )
            events_to_insert.append(evt_completed)

        self.event_repo.batch_insert_idempotent(events_to_insert)
            
        session_obj.state_snapshot = medha_state.to_dict()
        self.db.commit()
        self.db.refresh(checkin)
        
        # Trigger Structured Model -> structured_score -> Unified PredictionResult -> Fusion Pipeline
        try:
            from backend.services.prediction_service import update_structured_prediction
            update_structured_prediction(
                db=self.db,
                case_id=session_obj.case_id,
                timepoint=session_obj.timepoint,
                features=medha_state.structured_features,
                session_id=session_obj.id,
            )
        except Exception as e:
            logger.warning(f"Failed to update structured prediction on answer submit: {e}")

        next_q_resp = None
        if checkin.current_question_id:
            for q in checkin.questions:
                if q.question_id == checkin.current_question_id:
                    next_q_resp = self._build_question_response(q)
                    break

        enriched_questions = [self._build_question_response(q) for q in checkin.questions]
        chk_resp = CheckInResponse(
            id=checkin.id,
            session_id=checkin.session_id,
            status=checkin.status,
            started_at=checkin.started_at,
            completed_at=checkin.completed_at,
            current_question_id=checkin.current_question_id,
            questions=enriched_questions,
        )

        return CheckInAnswerResponse(
            status=checkin.status,
            checkin=chk_resp,
            next_question=next_q_resp
        )

    def _build_question_response(self, q: QuestionRecordModel) -> QuestionResponse:
        q_meta = next((item for item in self.question_engine.questions if item.get("question_id") == q.question_id), {})
        response_type = q_meta.get("response_type", "scale_1_5")
        
        prefix = q.question_id.split("-")[0] if "-" in q.question_id else q.question_id[:2]
        domain_map = {
            "GW": "General Wellbeing & Mood",
            "SF": "Sleep & Daytime Functioning",
            "ES": "Stress & Coping",
            "SA": "Safety & Stability",
            "SE": "Social Support & Connection",
        }
        domain = domain_map.get(prefix, "Clinical Assessment")
        
        if q.question_id == "SF-02":
            options = ["Fully", "Mostly", "Partially", "Not at all"]
        elif q.question_id == "GW-05":
            options = ["Better", "Worse", "About the same", "Prefer not to say"]
        elif q.question_id == "SA-03":
            options = ["All of them", "Some, not all", "None"]
        elif q.question_id == "ES-03":
            options = ["Never", "Rarely", "Sometimes", "Often", "Very often"]
        elif q.question_id == "SA-01":
            options = ["Yes, I feel safe", "No, I feel unsafe"]
        elif q.question_id == "SA-02":
            options = ["No threat", "Yes, active threat"]
        elif q.question_id == "SA-04":
            options = ["Yes, I have support", "No, I am alone"]
        elif response_type in ("yes_no", "binary"):
            options = ["Yes", "No"]
        elif response_type == "scale_1_5":
            if prefix in ("ES",):
                options = ["1 - Minimal", "2 - Mild", "3 - Moderate", "4 - Severe", "5 - Extreme"]
            elif prefix in ("GW", "SE", "SF"):
                options = ["1 - Very Low", "2 - Low", "3 - Moderate", "4 - Good", "5 - Optimal"]
            else:
                options = ["1 - Low", "2 - Mild", "3 - Moderate", "4 - Good", "5 - High"]
        elif response_type == "multiple_choice":
            options = ["Better", "Worse", "About the same", "Prefer not to say"]
        else:
            options = ["1 - Low", "2 - Mild", "3 - Moderate", "4 - Good", "5 - High"]

        return QuestionResponse(
            id=q.id,
            question_id=q.question_id,
            question_text=q.question_text,
            question_order=q.question_order,
            domain=domain,
            response_type=response_type,
            options=options,
            answered_at=q.answered_at,
            answer_status=q.answer_status,
        )

    def get_today_checkin_status(self, current_user: User) -> Dict[str, Any]:
        """
        Returns check-in status for today:
        - completed_today: True if a check-in was completed in the last 20 hours
        - active_checkin_id: UUID string if an in-progress check-in exists
        - status: "COMPLETED", "IN_PROGRESS", or "PENDING"
        """
        victim_id = None
        if hasattr(current_user, "cases") and current_user.cases:
            victim_id = current_user.cases[0].victim_id
        elif hasattr(current_user, "case") and current_user.case:
            victim_id = current_user.case.victim_id
        elif hasattr(current_user, "assigned_cases") and current_user.assigned_cases:
            victim_id = current_user.assigned_cases[0].victim_id

        if not victim_id:
            from backend.persistence.models.case import Case
            c = self.db.query(Case).filter(Case.user_id == current_user.id).first()
            if c:
                victim_id = c.victim_id
            else:
                victim_id = str(current_user.id)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=20)

        recent_checkins = (
            self.db.query(CheckInModel)
            .filter(CheckInModel.victim_id == victim_id)
            .order_by(CheckInModel.created_at.desc())
            .all()
        )

        completed_today = False
        active_checkin_id = None
        latest_status = "PENDING"

        for chk in recent_checkins:
            if chk.status == CheckInStatus.IN_PROGRESS.value:
                active_checkin_id = str(chk.id)
                latest_status = "IN_PROGRESS"
                break
            elif chk.status == CheckInStatus.COMPLETED.value:
                chk_comp = chk.completed_at
                if chk_comp:
                    if chk_comp.tzinfo is None:
                        chk_comp = chk_comp.replace(tzinfo=timezone.utc)
                    if chk_comp >= cutoff:
                        completed_today = True
                        latest_status = "COMPLETED"
                        break

        return {
            "completed_today": completed_today,
            "active_checkin_id": active_checkin_id,
            "status": latest_status,
        }

    def complete_checkin(self, checkin_id: uuid.UUID, current_user: User) -> CheckInResponse:
        checkin = self.checkin_repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        
        session_obj = self._verify_session_access(checkin.session_id, current_user)
        
        if checkin.status == CheckInStatus.COMPLETED.value:
            enriched_questions = [self._build_question_response(q) for q in checkin.questions]
            return CheckInResponse(
                id=checkin.id,
                session_id=checkin.session_id,
                status=checkin.status,
                started_at=checkin.started_at,
                completed_at=checkin.completed_at,
                current_question_id=checkin.current_question_id,
                questions=enriched_questions,
            )

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

        # Trigger Structured Model -> structured_score -> Unified PredictionResult -> Fusion Pipeline
        if session_obj.state_snapshot:
            try:
                from backend.services.prediction_service import update_structured_prediction
                struct_feats = session_obj.state_snapshot.get("structured_features", {})
                update_structured_prediction(
                    db=self.db,
                    case_id=session_obj.case_id,
                    timepoint=session_obj.timepoint,
                    features=struct_feats,
                    session_id=session_obj.id,
                )
            except Exception as e:
                logger.warning(f"Failed to update structured prediction on complete: {e}")

        enriched_questions = [self._build_question_response(q) for q in checkin.questions]
        return CheckInResponse(
            id=checkin.id,
            session_id=checkin.session_id,
            status=checkin.status,
            started_at=checkin.started_at,
            completed_at=checkin.completed_at,
            current_question_id=checkin.current_question_id,
            questions=enriched_questions,
        )
