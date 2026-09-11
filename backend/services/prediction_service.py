import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.integrations.medha_v2 import run_v2_inference

def get_latest_session(db: Session, case_id: uuid.UUID, timepoint: int) -> Optional[SessionModel]:
    return db.query(SessionModel).filter(
        SessionModel.case_id == case_id,
        SessionModel.timepoint == timepoint
    ).order_by(desc(SessionModel.updated_at)).first()

def get_latest_session_state(db: Session, case_id: uuid.UUID, timepoint: int) -> Dict[str, Any]:
    session_model = get_latest_session(db, case_id, timepoint)
    if session_model and session_model.state_snapshot:
        return session_model.state_snapshot
    return {}

def get_behaviour_snapshot(db: Session, case_id: uuid.UUID, timepoint: int) -> Optional[BehaviourFeatureSnapshotModel]:
    return db.query(BehaviourFeatureSnapshotModel).filter(
        BehaviourFeatureSnapshotModel.case_id == case_id,
        BehaviourFeatureSnapshotModel.timepoint == timepoint
    ).first()

def map_behaviour_to_v2(snapshot: Optional[BehaviourFeatureSnapshotModel]) -> Dict[str, Any]:
    if not snapshot:
        return {}
    return {
        "App_Interaction_Duration": snapshot.app_interaction_duration,
        "Engagement_Deviation": snapshot.app_interaction_duration_deviation,
        "Checkin_Response_Delay": snapshot.checkin_response_delay,
        "Response_Delay_Deviation": snapshot.checkin_response_delay_deviation,
        "Checkin_Completion_Rate": snapshot.checkin_completion_rate,
        "Missed_Checkin_Count": snapshot.missed_checkin_count,
        "Journal_Entry_Count": snapshot.journal_entry_count,
        "Chat_Message_Count": snapshot.chat_message_count,
        "Late_Night_Usage_Ratio": snapshot.late_night_usage_ratio,
        "Support_Resource_Access_Count": snapshot.support_resource_access_count,
    }

def generate_predictions(db: Session, case_id: uuid.UUID, timepoint: int) -> PredictionResultModel:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    latest_session = get_latest_session(db, case_id, timepoint)
    state_snapshot = latest_session.state_snapshot if latest_session and latest_session.state_snapshot else {}
    behav_snapshot = get_behaviour_snapshot(db, case_id, timepoint)

    # 1. Aggregate Features
    current_features = {}
    
    # 1a. From MedhaState (Text, Voice, Structured)
    current_features.update(state_snapshot.get("structured_features", {}))
    current_features.update(state_snapshot.get("text_features", {}))
    current_features.update(state_snapshot.get("voice_features", {}))
    
    current_features["Struct_Available"] = state_snapshot.get("struct_available", 0.0)
    current_features["Text_Available"] = state_snapshot.get("text_available", 0.0)
    current_features["Voice_Available"] = state_snapshot.get("voice_available", 0.0)
    current_features["Behav_Available"] = 1.0 if behav_snapshot else 0.0
    
    # 1b. From Behaviour
    behav_features = map_behaviour_to_v2(behav_snapshot)
    current_features.update(behav_features)

    # 2. Call V2 Pipeline
    predictions = run_v2_inference(case.victim_id, timepoint, current_features)

    # 3. Apply Triage Logic based on fusion
    triage_level = "UNKNOWN"
    fusion_score = predictions.get("Fusion_DDS_Prediction")
    if fusion_score is not None:
        if fusion_score >= 80:
            triage_level = "CRITICAL"
        elif fusion_score >= 60:
            triage_level = "HIGH"
        elif fusion_score >= 40:
            triage_level = "MEDIUM"
        else:
            triage_level = "LOW"

    # 4. Create PredictionResultModel
    prediction_record = PredictionResultModel(
        case_id=case_id,
        timepoint=timepoint,
        struct_pred=predictions.get("Struct_Pred"),
        text_pred=predictions.get("Text_Pred"),
        voice_pred=predictions.get("Voice_Pred"),
        behav_pred=predictions.get("Behav_Pred"),
        fusion_dds_prediction=predictions.get("Fusion_DDS_Prediction"),
        temporal_risk_score=predictions.get("Temporal_Risk_Score"),
        future_escalation_flag=predictions.get("Future_Escalation_Flag"),
        triage_level=triage_level,
        struct_available=bool(current_features["Struct_Available"]),
        text_available=bool(current_features["Text_Available"]),
        voice_available=bool(current_features["Voice_Available"]),
        behav_available=bool(current_features["Behav_Available"]),
        session_id=latest_session.id if latest_session else None
    )

    db.add(prediction_record)
    db.commit()
    db.refresh(prediction_record)

    return prediction_record
