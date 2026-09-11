"""
Unified Prediction Service
==========================

Centralized single source of truth for MEDHA multi-modal predictions.
Maintains exactly one PredictionResultModel record per assessment/session/day.

Modality Workflow:
  Questionnaire  -> Structured Model -> Update structured_score
  Journal        -> Text Model       -> Update text_score
  Voice Check-in -> Voice Model      -> Update voice_score
  Behaviour      -> Behaviour Model  -> Update behaviour_score

Once required modalities are available, executes the Fusion DDS Model:
  -> fusion_score, triage_level, explanation, recommendation

Independently, evaluates the Temporal GRU on the last 7 daily prediction records
to forecast Day-8 escalation risk into:
  -> temporal_risk, future_escalation_flag

Fields not yet generated remain strictly NULL (never NaN).
Each model updates only its own fields without overwriting other outputs.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import torch
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.integrations.medha_v2 import get_v2_pipeline, run_v2_inference
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.case import Case
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.session import SessionModel
from backend.services.checkin_service import QUESTION_TO_FEATURE_MAP

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text Feature Extractor
# ---------------------------------------------------------------------------

def extract_text_features(text: str) -> Dict[str, float]:
    """
    Extracts canonical MEDHA V2 text features from text content:
    Text_Distress, Fear, Threat_Context, Negative_Affect, Urgency (0.0 to 1.0)
    """
    if not text:
        return {
            "Text_Distress": 0.1,
            "Fear": 0.05,
            "Threat_Context": 0.0,
            "Negative_Affect": 0.1,
            "Urgency": 0.0,
        }

    lowered = text.lower()
    distress_words = [
        "sad", "depressed", "hopeless", "crying", "miserable", "hurt", "pain",
        "broken", "empty", "lonely", "lost", "struggling", "exhausted", "tired"
    ]
    fear_words = [
        "scared", "afraid", "terrified", "panic", "anxious", "nervous", "fear",
        "dread", "worry", "frightened", "nightmare"
    ]
    threat_words = [
        "threat", "danger", "harm", "violence", "abuse", "kill", "attack",
        "unsafe", "stalker", "trapped"
    ]
    neg_words = [
        "bad", "hate", "terrible", "awful", "horrible", "worst", "angry",
        "frustrated", "guilt", "shame", "worthless", "failure"
    ]
    urgency_words = [
        "immediately", "emergency", "crisis", "help", "can't take it",
        "urgent", "now", "stop", "please"
    ]

    def count_matches(words):
        return sum(1 for w in words if w in lowered)

    d_count = count_matches(distress_words)
    f_count = count_matches(fear_words)
    t_count = count_matches(threat_words)
    n_count = count_matches(neg_words)
    u_count = count_matches(urgency_words)

    text_distress = min(1.0, max(0.05, 0.15 + d_count * 0.2 + n_count * 0.1))
    fear = min(1.0, max(0.05, 0.10 + f_count * 0.25))
    threat = min(1.0, max(0.0, t_count * 0.35))
    negative_affect = min(1.0, max(0.05, 0.10 + n_count * 0.2 + d_count * 0.1))
    urgency = min(1.0, max(0.0, u_count * 0.3 + (0.2 if threat > 0.3 else 0.0)))

    return {
        "Text_Distress": round(text_distress, 4),
        "Fear": round(fear, 4),
        "Threat_Context": round(threat, 4),
        "Negative_Affect": round(negative_affect, 4),
        "Urgency": round(urgency, 4),
    }


# ---------------------------------------------------------------------------
# Single Source of Truth Prediction Record Access
# ---------------------------------------------------------------------------

def get_or_create_daily_prediction(
    db: Session,
    case_id: uuid.UUID,
    timepoint: int,
    session_id: Optional[uuid.UUID] = None,
) -> PredictionResultModel:
    """
    Returns the single centralized PredictionResultModel record for a given
    case and timepoint/day. If none exists, initializes one with all scores
    set to NULL (never NaN).
    """
    stmt = (
        select(PredictionResultModel)
        .where(
            PredictionResultModel.case_id == case_id,
            PredictionResultModel.timepoint == timepoint,
        )
        .order_by(PredictionResultModel.created_at.desc())
    )
    record = db.scalars(stmt).first()

    if record is not None:
        if session_id and not record.session_id:
            record.session_id = session_id
            db.commit()
        return record

    # Initialize single source of truth record
    now = datetime.now(timezone.utc)
    new_record = PredictionResultModel(
        case_id=case_id,
        session_id=session_id,
        timepoint=timepoint,
        structured_score=None,
        text_score=None,
        voice_score=None,
        behaviour_score=None,
        fusion_score=None,
        temporal_risk=None,
        future_escalation_flag=None,
        triage_level="UNKNOWN",
        explanation=None,
        recommendation=None,
        struct_available=False,
        text_available=False,
        voice_available=False,
        behav_available=False,
        predicted_at=now,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


# ---------------------------------------------------------------------------
# Specialist Update Handlers
# ---------------------------------------------------------------------------

def update_structured_prediction(
    db: Session,
    case_id: uuid.UUID,
    timepoint: int,
    features: Dict[str, Any],
    session_id: Optional[uuid.UUID] = None,
) -> PredictionResultModel:
    """
    Executes the Structured Model on check-in/questionnaire features,
    updates structured_score and struct_available, and triggers the Fusion Pipeline.
    """
    prediction = get_or_create_daily_prediction(db, case_id, timepoint, session_id)
    pipeline = get_v2_pipeline()

    # Construct input vector for structured preprocessor
    row = {}
    for feat in pipeline.structured_features:
        val = features.get(feat)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            row[feat] = np.nan
        else:
            row[feat] = float(val)

    df = pd.DataFrame([row])
    X_struct = pipeline.struct_preproc.transform(df[pipeline.structured_features])
    score = float(np.round(pipeline.struct_model.predict(X_struct)[0], 4))

    # Update structured fields only
    prediction.structured_score = score
    prediction.struct_available = True
    prediction.predicted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prediction)

    # Trigger downstream fusion & temporal evaluation
    return execute_fusion_and_temporal(db, prediction)


def update_text_prediction(
    db: Session,
    case_id: uuid.UUID,
    timepoint: int,
    text_content: str,
    session_id: Optional[uuid.UUID] = None,
) -> PredictionResultModel:
    """
    Extracts text distress features from journal entry or conversational text,
    runs Text Specialist model, updates text_score, and triggers Fusion.
    """
    prediction = get_or_create_daily_prediction(db, case_id, timepoint, session_id)
    pipeline = get_v2_pipeline()

    # Extract 5 core features
    text_features = extract_text_features(text_content)
    df = pd.DataFrame([text_features])

    X_text = pipeline.text_preproc.transform(df[pipeline.text_features])
    score = float(np.round(pipeline.text_model.predict(X_text)[0], 4))

    # Update text fields only
    prediction.text_score = score
    prediction.text_available = True
    prediction.predicted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prediction)

    # Trigger downstream fusion & temporal evaluation
    return execute_fusion_and_temporal(db, prediction)


def update_voice_prediction(
    db: Session,
    case_id: uuid.UUID,
    timepoint: int,
    voice_features: Dict[str, Any],
    session_id: Optional[uuid.UUID] = None,
) -> PredictionResultModel:
    """
    Runs Voice Specialist model on extracted acoustic features,
    updates voice_score, and triggers Fusion.
    """
    prediction = get_or_create_daily_prediction(db, case_id, timepoint, session_id)
    pipeline = get_v2_pipeline()

    row = {}
    for feat in pipeline.voice_features:
        row[feat] = float(voice_features.get(feat, 0.0) or 0.0)

    df = pd.DataFrame([row])
    X_voice = pipeline.voice_preproc.transform(df[pipeline.voice_features])
    score = float(np.round(pipeline.voice_model.predict(X_voice)[0], 4))

    # Update voice fields only
    prediction.voice_score = score
    prediction.voice_available = True
    prediction.predicted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prediction)

    # Trigger downstream fusion & temporal evaluation
    return execute_fusion_and_temporal(db, prediction)


def update_behaviour_prediction(
    db: Session,
    case_id: uuid.UUID,
    timepoint: int,
    behav_snapshot: Optional[BehaviourFeatureSnapshotModel],
    session_id: Optional[uuid.UUID] = None,
) -> PredictionResultModel:
    """
    Runs Behaviour Specialist on telemetry snapshot, updates behaviour_score,
    and triggers Fusion.
    """
    prediction = get_or_create_daily_prediction(db, case_id, timepoint, session_id)
    pipeline = get_v2_pipeline()

    behav_map = map_behaviour_to_v2(behav_snapshot)
    row = {}
    for feat in pipeline.behaviour_features_all:
        row[feat] = float(behav_map.get(feat, np.nan))

    df = pd.DataFrame([row])
    if "Engagement_Deviation" in df.columns:
        df["Engagement_Deviation"] = df["Engagement_Deviation"].abs()
    if "Response_Delay_Deviation" in df.columns:
        df["Response_Delay_Deviation"] = df["Response_Delay_Deviation"].abs()

    X_behav_imp = pd.DataFrame(
        pipeline.behav_preproc.transform(df[pipeline.behaviour_features_all]),
        columns=pipeline.behaviour_features_all
    )
    score = float(np.round(pipeline.behav_model.predict(X_behav_imp)[0], 4))

    # Update behaviour fields only
    prediction.behaviour_score = score
    prediction.behav_available = True
    prediction.predicted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prediction)

    # Trigger downstream fusion & temporal evaluation
    return execute_fusion_and_temporal(db, prediction)


# ---------------------------------------------------------------------------
# Fusion & Temporal Evaluation Pipeline
# ---------------------------------------------------------------------------

def execute_fusion_and_temporal(
    db: Session,
    prediction: PredictionResultModel,
) -> PredictionResultModel:
    """
    Executes the Fusion Model once any modality score is available, updates
    fusion_score, triage_level, explanation, recommendation, and runs the
    Temporal GRU on 7-day longitudinal history.
    """
    pipeline = get_v2_pipeline()

    # 1. Execute Fusion Model if at least one modality is available
    if any([
        prediction.struct_available,
        prediction.text_available,
        prediction.voice_available,
        prediction.behav_available,
    ]):
        fusion_row = {}
        for feat in pipeline.fusion_features:
            if feat == "Struct_Pred":
                fusion_row[feat] = prediction.structured_score if prediction.struct_available else 0.0
            elif feat == "Text_Pred":
                fusion_row[feat] = prediction.text_score if prediction.text_available else 0.0
            elif feat == "Voice_Pred":
                fusion_row[feat] = prediction.voice_score if prediction.voice_available else 0.0
            elif feat == "Behav_Pred":
                fusion_row[feat] = prediction.behaviour_score if prediction.behav_available else 0.0
            elif feat == "Struct_Available":
                fusion_row[feat] = 1.0 if prediction.struct_available else 0.0
            elif feat == "Text_Available":
                fusion_row[feat] = 1.0 if prediction.text_available else 0.0
            elif feat == "Voice_Available":
                fusion_row[feat] = 1.0 if prediction.voice_available else 0.0
            elif feat == "Behav_Available":
                fusion_row[feat] = 1.0 if prediction.behav_available else 0.0
            else:
                fusion_row[feat] = 0.0

        fusion_df = pd.DataFrame([fusion_row])[pipeline.fusion_features].fillna(0.0)
        fusion_val = float(np.clip(pipeline.fusion_model.predict(fusion_df.values)[0], 0.0, 100.0))
        prediction.fusion_score = float(np.round(fusion_val, 4))

        # Assign clinical triage level
        if fusion_val >= 80.0:
            prediction.triage_level = "CRITICAL"
        elif fusion_val >= 60.0:
            prediction.triage_level = "HIGH"
        elif fusion_val >= 40.0:
            prediction.triage_level = "MEDIUM"
        else:
            prediction.triage_level = "LOW"

        # Generate Explainability & Recommendation outputs
        try:
            case = db.query(Case).filter(Case.id == prediction.case_id).first()
            if case:
                from backend.services.insights_service import InsightService
                from backend.services.recommendation_service import RecommendationService

                insights = InsightService().get_case_insights(db, case, session_id=prediction.session_id)
                prediction.explanation = insights.summary

                recs = RecommendationService().get_case_recommendations(db, case, session_id=prediction.session_id)
                if recs and recs.recommendations:
                    top_recs = [f"[{r.priority.upper()}] {r.action}: {r.reason}" for r in recs.recommendations[:3]]
                    prediction.recommendation = " | ".join(top_recs)
                else:
                    prediction.recommendation = "Continue routine longitudinal monitoring."
        except Exception as e:
            logger.warning(f"Clinical explainability / recommendation generation failed: {e}")

    # 2. Independently evaluate Temporal GRU on last 7 daily prediction records
    historical_records = (
        db.query(PredictionResultModel)
        .filter(
            PredictionResultModel.case_id == prediction.case_id,
            PredictionResultModel.timepoint <= prediction.timepoint,
        )
        .order_by(PredictionResultModel.timepoint.asc())
        .all()
    )

    if len(historical_records) >= 7:
        try:
            last_7 = historical_records[-7:]
            # Build sequence window of shape (7, len(pipeline.gru_features))
            seq_rows = []
            for rec in last_7:
                row = {}
                for feat in pipeline.gru_features:
                    if feat == "Struct_Pred":
                        row[feat] = rec.structured_score or 0.0
                    elif feat == "Text_Pred":
                        row[feat] = rec.text_score or 0.0
                    elif feat == "Voice_Pred":
                        row[feat] = rec.voice_score or 0.0
                    elif feat == "Behav_Pred":
                        row[feat] = rec.behaviour_score or 0.0
                    elif feat == "Fusion_DDS_Prediction":
                        row[feat] = rec.fusion_score or 0.0
                    else:
                        row[feat] = 0.0
                seq_rows.append(row)

            window_df = pd.DataFrame(seq_rows)[pipeline.gru_features].fillna(0.0).astype(np.float32)
            window_scaled = pipeline.gru_scaler.transform(window_df.values)

            with torch.no_grad():
                tensor_x = torch.from_numpy(window_scaled).unsqueeze(0).to(pipeline.device)
                prob = pipeline.gru_model.predict_proba(tensor_x).item()

            prediction.temporal_risk = float(np.round(prob, 4))
            prediction.future_escalation_flag = int(prob >= pipeline.gru_threshold)
        except Exception as e:
            logger.warning(f"Temporal GRU sequence inference failed: {e}")
            prediction.temporal_risk = None
            prediction.future_escalation_flag = None
    else:
        # History < 7 days: remains NULL, not NaN
        prediction.temporal_risk = None
        prediction.future_escalation_flag = None

    prediction.predicted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prediction)
    return prediction


# ---------------------------------------------------------------------------
# Backward-Compatible Full State Aggregator
# ---------------------------------------------------------------------------

def get_latest_session_state(db: Session, case_id: uuid.UUID, timepoint: int) -> Dict[str, Any]:
    session_model = db.query(SessionModel).filter(
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
    """
    Aggregates available observations from session snapshots, check-in answers,
    and behaviour snapshots, runs the V2 pipeline, and updates the single source of truth record.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    latest_session = get_latest_session(db, case_id, timepoint)
    state_snapshot = latest_session.state_snapshot if latest_session and latest_session.state_snapshot else {}
    behav_snapshot = get_behaviour_snapshot(db, case_id, timepoint)

    # 1. Aggregate Features
    current_features = {}
    current_features.update(state_snapshot.get("structured_features", {}))
    current_features.update(state_snapshot.get("text_features", {}))
    current_features.update(state_snapshot.get("voice_features", {}))

    availabilities = state_snapshot.get("modality_availability", {})
    current_features["Struct_Available"] = availabilities.get("structured", 0.0)
    current_features["Text_Available"] = availabilities.get("text", 0.0)
    current_features["Voice_Available"] = availabilities.get("voice", 0.0)
    current_features["Behav_Available"] = 1.0 if behav_snapshot else 0.0

    behav_features = map_behaviour_to_v2(behav_snapshot)
    current_features.update(behav_features)

    # 1c. Augment directly from answered check-in questions for this case up to timepoint
    checkin_q_rows = (
        db.query(QuestionRecordModel)
        .join(CheckInModel, QuestionRecordModel.checkin_id == CheckInModel.id)
        .join(SessionModel, CheckInModel.session_id == SessionModel.id)
        .filter(
            SessionModel.case_id == case_id,
            SessionModel.timepoint <= timepoint,
            QuestionRecordModel.answer_status == "answered",
        )
        .order_by(QuestionRecordModel.answered_at.asc())
        .all()
    )

    if checkin_q_rows:
        current_features["Checkin_Available"] = 1.0
        current_features["Struct_Available"] = 1.0
        for q in checkin_q_rows:
            feat_name = QUESTION_TO_FEATURE_MAP.get(q.question_id)
            if feat_name and q.answer:
                vals = list(q.answer.values())
                if vals:
                    v = vals[0]
                    try:
                        num_v = 1.0 if v is True else (0.0 if v is False else float(v))
                        current_features[feat_name] = num_v
                        if feat_name == "Self_Reported_Wellbeing":
                            current_features["Mood"] = num_v
                    except Exception:
                        pass

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

    # 4. Update single source of truth PredictionResultModel record
    prediction = get_or_create_daily_prediction(db, case_id, timepoint)
    prediction.structured_score = predictions.get("Struct_Pred")
    prediction.text_score = predictions.get("Text_Pred")
    prediction.voice_score = predictions.get("Voice_Pred")
    prediction.behaviour_score = predictions.get("Behav_Pred")
    prediction.fusion_score = predictions.get("Fusion_DDS_Prediction")
    prediction.temporal_risk = predictions.get("Temporal_Risk_Score")
    prediction.future_escalation_flag = predictions.get("Future_Escalation_Flag")
    prediction.triage_level = triage_level
    prediction.struct_available = bool(current_features["Struct_Available"])
    prediction.text_available = bool(current_features["Text_Available"])
    prediction.voice_available = bool(current_features["Voice_Available"])
    prediction.behav_available = bool(current_features["Behav_Available"])
    prediction.predicted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prediction)
    return prediction
