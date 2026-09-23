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

import sys
from pathlib import Path

from backend.integrations.medha_v2 import get_v2_pipeline, run_v2_inference
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.case import Case
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.session import SessionModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.clinical_event import ClinicalEventModel
from backend.services.checkin_service import QUESTION_TO_FEATURE_MAP

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text Feature Extractor (MuRIL V2 with Graceful Heuristic Fallback)
# ---------------------------------------------------------------------------

_TEXT_ENGINE_FN = None


def _get_text_engine():
    """Lazily loads the standardized MuRIL text engine wrapper."""
    global _TEXT_ENGINE_FN
    if _TEXT_ENGINE_FN is None:
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent
            text_engine_path = str(repo_root / "engine" / "text engine")
            if text_engine_path not in sys.path:
                sys.path.insert(0, text_engine_path)
            from medha_text_engine import medha_text_engine
            _TEXT_ENGINE_FN = medha_text_engine
            logger.info("Successfully loaded MEDHA MuRIL deep text engine.")
        except Exception as e:
            logger.warning(f"Could not load MEDHA MuRIL text engine, using fallback: {e}")
            _TEXT_ENGINE_FN = False
    return _TEXT_ENGINE_FN if _TEXT_ENGINE_FN is not False else None


def extract_text_features(text: str, source: str = "diary") -> Dict[str, float]:
    """
    Extracts canonical MEDHA V2 text features from text content:
    Text_Distress, Fear, Threat_Context, Negative_Affect, Urgency (0.0 to 1.0)
    using the fine-tuned MuRIL transformer model, with robust heuristic fallback.
    """
    if not text or not str(text).strip():
        return {
            "Text_Distress": 0.1,
            "Fear": 0.05,
            "Threat_Context": 0.0,
            "Negative_Affect": 0.1,
            "Urgency": 0.0,
        }

    engine_fn = _get_text_engine()
    if engine_fn is not None:
        try:
            req = {
                "text": str(text).strip(),
                "source": source,
            }
            res = engine_fn(req)
            raw_vec = res.get("text_vector", {})
            if raw_vec and "text_distress" in raw_vec:
                return {
                    "Text_Distress": float(raw_vec["text_distress"]),
                    "Fear": float(raw_vec["fear_signal"]),
                    "Threat_Context": float(raw_vec["threat_context"]),
                    "Negative_Affect": float(raw_vec["negative_affect"]),
                    "Urgency": float(raw_vec["urgency"]),
                }
        except Exception as e:
            logger.warning(f"MuRIL text engine inference failed, falling back to heuristic: {e}")

    # Fallback keyword matching heuristic
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
    case and timepoint/day. Automatically reconciles and merges any duplicate records
    to ensure exactly one authoritative source of truth exists.
    """
    records = (
        db.query(PredictionResultModel)
        .filter(
            PredictionResultModel.case_id == case_id,
            PredictionResultModel.timepoint == timepoint,
        )
        .order_by(PredictionResultModel.created_at.asc())
        .all()
    )

    if records:
        canonical = records[-1]
        if len(records) > 1:
            for other in records[:-1]:
                if canonical.structured_score is None and other.structured_score is not None:
                    canonical.structured_score = other.structured_score
                    canonical.struct_available = True
                if canonical.text_score is None and other.text_score is not None:
                    canonical.text_score = other.text_score
                    canonical.text_available = True
                if canonical.voice_score is None and other.voice_score is not None:
                    canonical.voice_score = other.voice_score
                    canonical.voice_available = True
                if canonical.behaviour_score is None and other.behaviour_score is not None:
                    canonical.behaviour_score = other.behaviour_score
                    canonical.behav_available = True
                if canonical.fusion_score is None and other.fusion_score is not None:
                    canonical.fusion_score = other.fusion_score
                if canonical.temporal_risk is None and other.temporal_risk is not None:
                    canonical.temporal_risk = other.temporal_risk
                if canonical.future_escalation_flag is None and other.future_escalation_flag is not None:
                    canonical.future_escalation_flag = other.future_escalation_flag
                if canonical.session_id is None and other.session_id is not None:
                    canonical.session_id = other.session_id
                db.delete(other)
            db.commit()

        if session_id and not canonical.session_id:
            canonical.session_id = session_id
            db.commit()
        return canonical

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
    source: str = "diary",
) -> PredictionResultModel:
    """
    Extracts text distress features from journal entry or conversational text,
    runs Text Specialist model, updates text_score, and triggers Fusion.
    """
    prediction = get_or_create_daily_prediction(db, case_id, timepoint, session_id)
    pipeline = get_v2_pipeline()

    # Extract 5 core features using fine-tuned MuRIL / fallback
    text_features = extract_text_features(text_content, source=source)
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

def build_longitudinal_gru_window(
    db: Session,
    case: Case,
    current_timepoint: int,
) -> pd.DataFrame:
    """
    Constructs the 7-day longitudinal sequence of 57 canonical features expected by
    the trained MEDHA V2 GRU model. Applies progressive baseline padding for sequences
    under 7 days so Day-8 escalation forecasting is always computed.
    """
    pipeline = get_v2_pipeline()
    daily_vectors = []

    tp_end = max(1, current_timepoint)
    for t in range(1, tp_end + 1):
        row = {f: 0.0 for f in pipeline.gru_features}

        # 1. Check-in questions
        q_rows = (
            db.query(QuestionRecordModel)
            .join(CheckInModel, QuestionRecordModel.checkin_id == CheckInModel.id)
            .join(SessionModel, CheckInModel.session_id == SessionModel.id)
            .filter(
                SessionModel.case_id == case.id,
                SessionModel.timepoint == t,
                QuestionRecordModel.answer_status == "answered",
            )
            .all()
        )
        if q_rows:
            row["Checkin_Available"] = 1.0
            for q in q_rows:
                feat_name = QUESTION_TO_FEATURE_MAP.get(q.question_id)
                if feat_name and q.answer:
                    vals = list(q.answer.values())
                    if vals:
                        v = vals[0]
                        try:
                            num_v = 1.0 if v is True else (0.0 if v is False else float(v))
                            row[feat_name] = num_v
                            if feat_name == "Self_Reported_Wellbeing":
                                row["Mood"] = num_v
                        except Exception:
                            pass
        else:
            row["Checkin_Available"] = 1.0 if t == 1 else 0.0
            row["Mood"] = 0.45
            row["Stress"] = 0.55
            row["Sleep"] = 0.4
            row["Functioning"] = 0.5
            row["Safety"] = 0.8
            row["Self_Reported_Wellbeing"] = 0.45

        # 2. Text Features from Journal or existing daily prediction
        journal = (
            db.query(JournalEntryModel)
            .filter(JournalEntryModel.case_id == case.id)
            .order_by(JournalEntryModel.created_at.desc())
            .first()
        )
        if journal and journal.content:
            tf = extract_text_features(journal.content, source="diary")
            row.update(tf)
            row["Text_Available"] = 1.0
            row["Diary_Available"] = 1.0
        else:
            p_rec = (
                db.query(PredictionResultModel)
                .filter(PredictionResultModel.case_id == case.id, PredictionResultModel.timepoint == t)
                .first()
            )
            if p_rec and p_rec.text_available and p_rec.text_score is not None:
                row["Text_Available"] = 1.0
                row["Text_Distress"] = round(p_rec.text_score / 100.0, 4)
                row["Fear"] = 0.25
                row["Threat_Context"] = 0.1
                row["Negative_Affect"] = 0.3
                row["Urgency"] = 0.1
            else:
                row["Text_Available"] = 0.0

        # 3. Voice Features from VoiceRecordModel
        voice_rec = (
            db.query(VoiceRecordModel)
            .filter(
                VoiceRecordModel.case_id == case.id,
                (VoiceRecordModel.timepoint == str(t))
                | (VoiceRecordModel.timepoint == f"T{t}")
                | (VoiceRecordModel.timepoint == "current")
            )
            .order_by(VoiceRecordModel.created_at.desc())
            .first()
        )
        if not voice_rec:
            voice_rec = (
                db.query(VoiceRecordModel)
                .filter(VoiceRecordModel.case_id == case.id)
                .order_by(VoiceRecordModel.created_at.desc())
                .first()
            )
        if voice_rec and voice_rec.extracted_features:
            row["Voice_Available"] = 1.0
            for vf in ["Voice_Distress", "Pause_Ratio", "Speech_Rate_Deviation", "Energy_Deviation", "Acoustic_Indicator"]:
                row[vf] = float(voice_rec.extracted_features.get(vf, 0.0) or 0.0)
        else:
            p_rec = (
                db.query(PredictionResultModel)
                .filter(PredictionResultModel.case_id == case.id, PredictionResultModel.timepoint == t)
                .first()
            )
            if p_rec and p_rec.voice_available and p_rec.voice_score is not None:
                row["Voice_Available"] = 1.0
                row["Voice_Distress"] = round(p_rec.voice_score / 100.0, 4)
                row["Pause_Ratio"] = 0.3
                row["Energy_Deviation"] = 0.35
            else:
                row["Voice_Available"] = 0.0

        # 4. Behaviour Features
        behav = (
            db.query(BehaviourFeatureSnapshotModel)
            .filter(BehaviourFeatureSnapshotModel.case_id == case.id, BehaviourFeatureSnapshotModel.timepoint == t)
            .first()
        )
        if behav:
            row["Engagement_Score"] = float(behav.app_interaction_duration or 300) / 600.0
            row["Engagement_Deviation"] = float(behav.app_interaction_duration_deviation or 0.0)
            row["Response_Delay_Hours"] = float(behav.checkin_response_delay or 3600) / 3600.0
            row["Response_Delay_Deviation"] = float(behav.checkin_response_delay_deviation or 0.0)
            row["Missed_Checkin"] = float(behav.missed_checkin_count or 0)
            row["Session_Duration_Minutes"] = float(behav.app_interaction_duration or 300) / 60.0
            row["Interaction_Frequency_7d"] = float(behav.chat_message_count or 1)

        # 5. Clinical Events & Protective Factors
        events = (
            db.query(ClinicalEventModel)
            .filter(ClinicalEventModel.case_id == case.id)
            .all()
        )
        for ev in events:
            if ev.event_type in ("CRISIS_INCIDENT", "Threat"):
                row["Threat_Event"] = 1.0
                row["Recent_Episode"] = 1.0
            elif ev.event_type == "PANIC_ATTACK":
                row["Recent_Episode"] = 1.0
            elif ev.event_type in ("MEDICATION_CHANGE", "SESSION_NOTE"):
                row["Therapist_Observation_Available"] = 1.0
                row["Therapist_Observation_Score"] = 0.5

        row["Family_Support"] = 1.0
        row["Social_Support"] = 1.0
        row["Access_To_Services"] = 1.0
        row["Stable_Housing"] = 1.0
        row["Therapist_Engagement"] = 1.0

        daily_vectors.append(row)

    # 6. Baselines & Trends
    day1 = daily_vectors[0]
    b_resp = day1.get("Response_Delay_Hours", 1.0)
    b_eng = day1.get("Engagement_Score", 0.5)
    b_text = day1.get("Text_Distress", 0.2)
    b_voice = day1.get("Voice_Distress", 0.2)
    b_chk = 1.0 - day1.get("Mood", 0.5)

    for i, d in enumerate(daily_vectors):
        d["Baseline_Response_Delay"] = b_resp
        d["Baseline_Engagement"] = b_eng
        d["Baseline_Text_Distress"] = b_text
        d["Baseline_Voice_Distress"] = b_voice
        d["Baseline_Checkin_Distress"] = b_chk
        d["Text_Distress_Deviation"] = d.get("Text_Distress", 0.0) - b_text
        d["Voice_Distress_Deviation"] = d.get("Voice_Distress", 0.0) - b_voice

        prev = daily_vectors[i - 1] if i > 0 else d
        d["Text_Distress_Trend"] = d.get("Text_Distress", 0.0) - prev.get("Text_Distress", 0.0)
        d["Voice_Distress_Trend"] = d.get("Voice_Distress", 0.0) - prev.get("Voice_Distress", 0.0)
        d["Engagement_Trend"] = d.get("Engagement_Score", 0.0) - prev.get("Engagement_Score", 0.0)

    # 7. Progressive sequence padding to 7 days
    padded = []
    needed = 7 - len(daily_vectors)
    if needed > 0:
        for _ in range(needed):
            padded.append(daily_vectors[0].copy())
    padded.extend(daily_vectors)
    padded = padded[-7:]

    return pd.DataFrame(padded)[pipeline.gru_features].fillna(0.0).astype(np.float32)


def execute_fusion_and_temporal(
    db: Session,
    prediction: PredictionResultModel,
) -> PredictionResultModel:
    """
    Executes the Fusion Model once any modality score is available, updates
    fusion_score, triage_level, explanation, recommendation, and runs the
    Temporal GRU on 7-day longitudinal history to forecast Day-8 escalation.
    """
    pipeline = get_v2_pipeline()

    # 1. Ensure Voice is considered if a voice record exists for this case/timepoint
    if not prediction.voice_available or prediction.voice_score is None:
        voice_rec = (
            db.query(VoiceRecordModel)
            .filter(
                VoiceRecordModel.case_id == prediction.case_id,
                (VoiceRecordModel.timepoint == str(prediction.timepoint))
                | (VoiceRecordModel.timepoint == f"T{prediction.timepoint}")
                | (VoiceRecordModel.timepoint == "current")
            )
            .order_by(VoiceRecordModel.created_at.desc())
            .first()
        )
        if not voice_rec:
            voice_rec = (
                db.query(VoiceRecordModel)
                .filter(VoiceRecordModel.case_id == prediction.case_id)
                .order_by(VoiceRecordModel.created_at.desc())
                .first()
            )
        if voice_rec:
            if voice_rec.voice_score is not None:
                prediction.voice_score = voice_rec.voice_score
                prediction.voice_available = True
            elif voice_rec.extracted_features:
                row = {}
                for feat in pipeline.voice_features:
                    row[feat] = float(voice_rec.extracted_features.get(feat, 0.0) or 0.0)
                df = pd.DataFrame([row])
                X_voice = pipeline.voice_preproc.transform(df[pipeline.voice_features])
                score = float(np.round(pipeline.voice_model.predict(X_voice)[0], 4))
                prediction.voice_score = score
                prediction.voice_available = True

    # 2. Execute Fusion Model if at least one modality is available
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

    # 3. Independently evaluate Temporal GRU on 7-day longitudinal sequence window to forecast Day-8 escalation
    try:
        case = db.query(Case).filter(Case.id == prediction.case_id).first()
        if case:
            window_df = build_longitudinal_gru_window(db, case, prediction.timepoint)
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

    prediction.predicted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prediction)
    return prediction


# ---------------------------------------------------------------------------
# Backward-Compatible Full State Aggregator
# ---------------------------------------------------------------------------

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

    # 1b. Augment text features from journal if not in state_snapshot
    if not current_features.get("Text_Available"):
        latest_journal = (
            db.query(JournalEntryModel)
            .filter(JournalEntryModel.case_id == case_id)
            .order_by(JournalEntryModel.created_at.desc())
            .first()
        )
        if latest_journal and latest_journal.content:
            journal_feats = extract_text_features(latest_journal.content, source="diary")
            current_features.update(journal_feats)
            current_features["Text_Available"] = 1.0

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

    # 1d. Augment voice features from VoiceRecordModel if not in current_features
    if not current_features.get("Voice_Available"):
        latest_voice = (
            db.query(VoiceRecordModel)
            .filter(VoiceRecordModel.case_id == case_id)
            .order_by(VoiceRecordModel.created_at.desc())
            .first()
        )
        if latest_voice and latest_voice.extracted_features:
            current_features.update(latest_voice.extracted_features)
            current_features["Voice_Available"] = 1.0
            if latest_voice.voice_score is not None:
                current_features["Voice_Pred"] = latest_voice.voice_score

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

    if predictions.get("Struct_Pred") is not None:
        prediction.structured_score = predictions.get("Struct_Pred")
        prediction.struct_available = True
    elif current_features.get("Struct_Available"):
        prediction.struct_available = True

    if predictions.get("Text_Pred") is not None:
        prediction.text_score = predictions.get("Text_Pred")
        prediction.text_available = True
    elif current_features.get("Text_Available"):
        prediction.text_available = True

    if predictions.get("Voice_Pred") is not None:
        prediction.voice_score = predictions.get("Voice_Pred")
        prediction.voice_available = True
    elif current_features.get("Voice_Pred") is not None:
        prediction.voice_score = current_features.get("Voice_Pred")
        prediction.voice_available = True
    elif current_features.get("Voice_Available"):
        prediction.voice_available = True

    if predictions.get("Behav_Pred") is not None:
        prediction.behaviour_score = predictions.get("Behav_Pred")
        prediction.behav_available = True
    elif current_features.get("Behav_Available"):
        prediction.behav_available = True

    if fusion_score is not None:
        prediction.fusion_score = fusion_score
    prediction.triage_level = triage_level

    # Execute 7-day longitudinal sequence evaluation for Day-8 escalation forecasting
    try:
        pipeline = get_v2_pipeline()
        window_df = build_longitudinal_gru_window(db, case, timepoint)
        window_scaled = pipeline.gru_scaler.transform(window_df.values)
        with torch.no_grad():
            tensor_x = torch.from_numpy(window_scaled).unsqueeze(0).to(pipeline.device)
            prob = pipeline.gru_model.predict_proba(tensor_x).item()
        prediction.temporal_risk = float(np.round(prob, 4))
        prediction.future_escalation_flag = int(prob >= pipeline.gru_threshold)
    except Exception as e:
        logger.warning(f"Temporal GRU sequence inference failed: {e}")

    prediction.predicted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prediction)
    return prediction
