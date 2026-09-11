"""
Demo Seed System
================

Populates realistic multi-case longitudinal demo data across the clinical
risk spectrum (LOW, MODERATE, HIGH, CRITICAL) for Dr. Eleanor Vance.

All predictions are generated strictly through the authentic V2 pipeline
via `backend.services.prediction_service.generate_predictions()`.
No hardcoded scores or fake PredictionResultModel entries are inserted.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel, CheckInStatus
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.event import RawEventModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.security.passwords import hash_password
from backend.services.prediction_service import generate_predictions

logger = logging.getLogger(__name__)

# Constants for Demo Credentials
DEMO_THERAPIST_EMAIL = "dr.vance@medha.test"
DEMO_THERAPIST_NAME = "Dr. Eleanor Vance"
DEMO_THERAPIST_PASSWORD = "DemoTherapist2026!"

DEMO_CASES_CONFIG = [
    {
        "patient_name": "Alice Low",
        "email": "alice.low@medha.test",
        "password": "DemoPatient2026!",
        "victim_id": "V-DEMO-LOW-001",
        "profile": "LOW",
        "summary": "Mild occasional fatigue, strong social support, resilient coping strategies.",
        "case_type": "DOMESTIC",
        "case_stage": "RECOVERY",
        "timepoints": [
            {
                "timepoint": 1,
                "days_ago": 14,
                "mood": 4.8,
                "wellbeing": 4.8,
                "stress": 1.2,
                "sleep": 4.8,
                "functioning": 4.8,
                "safety": 4.8,
                "social_support": 4.8,
                "recent_episode": 0.0,
                "episode_severity": 0.0,
                "threat_event": 0.0,
                "chat_user_msg": "I've been feeling pretty good this week. Spending time with family helped a lot.",
                "chat_assistant_msg": "I'm glad to hear that you're feeling well and finding support in your family.",
                "text_distress": 0.10,
                "fear": 0.05,
                "threat_context": 0.0,
                "negative_affect": 0.08,
                "urgency": 0.05,
                "voice_distress": 0.12,
                "pause_ratio": 0.10,
                "speech_rate_dev": 0.05,
                "energy_dev": 0.04,
                "acoustic_indicator": 0.10,
                "interaction_duration": 420.0,
                "response_delay": 2.0,
                "response_delay_dev": -1.0,
                "late_night_ratio": 0.0,
                "missed_checkins": 0,
                "engagement_score": 0.88,
                "engagement_dev": 0.10,
                "b_trend": -0.04,
            },
            {
                "timepoint": 2,
                "days_ago": 7,
                "mood": 4.6,
                "wellbeing": 4.6,
                "stress": 1.5,
                "sleep": 4.6,
                "functioning": 4.6,
                "safety": 4.8,
                "social_support": 4.6,
                "recent_episode": 0.0,
                "episode_severity": 0.0,
                "threat_event": 0.0,
                "chat_user_msg": "Things are still going well, just a little busy with work projects.",
                "chat_assistant_msg": "That sounds manageable. Remember to take short breaks when needed.",
                "text_distress": 0.12,
                "fear": 0.06,
                "threat_context": 0.0,
                "negative_affect": 0.10,
                "urgency": 0.06,
                "voice_distress": 0.14,
                "pause_ratio": 0.11,
                "speech_rate_dev": 0.06,
                "energy_dev": 0.05,
                "acoustic_indicator": 0.12,
                "interaction_duration": 390.0,
                "response_delay": 2.2,
                "response_delay_dev": -0.8,
                "late_night_ratio": 0.02,
                "missed_checkins": 0,
                "engagement_score": 0.85,
                "engagement_dev": 0.08,
                "b_trend": -0.03,
            },
            {
                "timepoint": 3,
                "days_ago": 0,
                "mood": 4.8,
                "wellbeing": 4.8,
                "stress": 1.3,
                "sleep": 4.8,
                "functioning": 4.9,
                "safety": 4.9,
                "social_support": 4.8,
                "recent_episode": 0.0,
                "episode_severity": 0.0,
                "threat_event": 0.0,
                "chat_user_msg": "Feeling steady and balanced. Daily walks have really improved my sleep.",
                "chat_assistant_msg": "Wonderful progress. Routine physical activity is a great anchor.",
                "text_distress": 0.09,
                "fear": 0.04,
                "threat_context": 0.0,
                "negative_affect": 0.07,
                "urgency": 0.04,
                "voice_distress": 0.11,
                "pause_ratio": 0.09,
                "speech_rate_dev": 0.04,
                "energy_dev": 0.03,
                "acoustic_indicator": 0.09,
                "interaction_duration": 450.0,
                "response_delay": 1.9,
                "response_delay_dev": -1.1,
                "late_night_ratio": 0.0,
                "missed_checkins": 0,
                "engagement_score": 0.90,
                "engagement_dev": 0.12,
                "b_trend": -0.05,
            },
        ],
    },
    {
        "patient_name": "Mark Moderate",
        "email": "mark.mod@medha.test",
        "password": "DemoPatient2026!",
        "victim_id": "V-DEMO-MOD-001",
        "profile": "MODERATE",
        "summary": "Moderate situational anxiety, academic deadlines, occasional sleep disruption.",
        "case_type": "HARASSMENT",
        "case_stage": "INVESTIGATION",
        "timepoints": [
            {
                "timepoint": 1,
                "days_ago": 14,
                "mood": 2.8,
                "wellbeing": 2.8,
                "stress": 3.5,
                "sleep": 2.8,
                "functioning": 3.0,
                "safety": 3.2,
                "social_support": 2.8,
                "recent_episode": 0.0,
                "episode_severity": 1.0,
                "threat_event": 0.0,
                "chat_user_msg": "I have been feeling stressed about my upcoming exams and not sleeping great.",
                "chat_assistant_msg": "Exam stress can certainly take a toll on sleep. Let's work on paced breathing.",
                "text_distress": 0.55,
                "fear": 0.45,
                "threat_context": 0.30,
                "negative_affect": 0.50,
                "urgency": 0.40,
                "voice_distress": 0.55,
                "pause_ratio": 0.22,
                "speech_rate_dev": 0.18,
                "energy_dev": 0.14,
                "acoustic_indicator": 0.50,
                "interaction_duration": 310.0,
                "response_delay": 7.0,
                "response_delay_dev": 1.5,
                "late_night_ratio": 0.15,
                "missed_checkins": 0,
                "engagement_score": 0.55,
                "engagement_dev": -0.10,
                "b_trend": 0.01,
            },
            {
                "timepoint": 2,
                "days_ago": 7,
                "mood": 2.5,
                "wellbeing": 2.5,
                "stress": 3.8,
                "sleep": 2.5,
                "functioning": 2.8,
                "safety": 3.0,
                "social_support": 2.5,
                "recent_episode": 0.0,
                "episode_severity": 1.5,
                "threat_event": 0.0,
                "chat_user_msg": "Still feeling a bit overwhelmed, but trying to stick to my study schedule.",
                "chat_assistant_msg": "Acknowledging the pressure is important. Breaking tasks into smaller steps can help.",
                "text_distress": 0.60,
                "fear": 0.50,
                "threat_context": 0.35,
                "negative_affect": 0.55,
                "urgency": 0.45,
                "voice_distress": 0.60,
                "pause_ratio": 0.24,
                "speech_rate_dev": 0.20,
                "energy_dev": 0.16,
                "acoustic_indicator": 0.55,
                "interaction_duration": 290.0,
                "response_delay": 8.5,
                "response_delay_dev": 2.5,
                "late_night_ratio": 0.20,
                "missed_checkins": 0,
                "engagement_score": 0.50,
                "engagement_dev": -0.15,
                "b_trend": 0.03,
            },
            {
                "timepoint": 3,
                "days_ago": 0,
                "mood": 2.9,
                "wellbeing": 2.9,
                "stress": 3.3,
                "sleep": 3.0,
                "functioning": 3.2,
                "safety": 3.4,
                "social_support": 3.0,
                "recent_episode": 0.0,
                "episode_severity": 0.8,
                "threat_event": 0.0,
                "chat_user_msg": "Finished the major exam today. Feeling slightly relieved although still tired.",
                "chat_assistant_msg": "Congratulations on finishing. Be sure to prioritize rest and recovery.",
                "text_distress": 0.50,
                "fear": 0.40,
                "threat_context": 0.25,
                "negative_affect": 0.45,
                "urgency": 0.35,
                "voice_distress": 0.50,
                "pause_ratio": 0.20,
                "speech_rate_dev": 0.15,
                "energy_dev": 0.12,
                "acoustic_indicator": 0.45,
                "interaction_duration": 340.0,
                "response_delay": 6.5,
                "response_delay_dev": 0.8,
                "late_night_ratio": 0.10,
                "missed_checkins": 0,
                "engagement_score": 0.60,
                "engagement_dev": -0.05,
                "b_trend": 0.00,
            },
        ],
    },
    {
        "patient_name": "Hannah High",
        "email": "hannah.high@medha.test",
        "password": "DemoPatient2026!",
        "victim_id": "V-DEMO-HIGH-001",
        "profile": "HIGH",
        "summary": "Severe depressive symptoms, social withdrawal, progressive deterioration.",
        "case_type": "STALKING",
        "case_stage": "TRIAL",
        "timepoints": [
            {
                "timepoint": 1,
                "days_ago": 14,
                "mood": 2.0,
                "wellbeing": 2.0,
                "stress": 4.2,
                "sleep": 2.0,
                "functioning": 2.2,
                "safety": 2.2,
                "social_support": 2.0,
                "recent_episode": 1.0,
                "episode_severity": 3.5,
                "threat_event": 0.0,
                "chat_user_msg": "I feel very disconnected from everyone. Getting out of bed is a struggle.",
                "chat_assistant_msg": "I hear how heavy things feel right now. We are here to support you step by step.",
                "text_distress": 0.78,
                "fear": 0.72,
                "threat_context": 0.60,
                "negative_affect": 0.75,
                "urgency": 0.70,
                "voice_distress": 0.78,
                "pause_ratio": 0.28,
                "speech_rate_dev": 0.35,
                "energy_dev": 0.30,
                "acoustic_indicator": 0.78,
                "interaction_duration": 180.0,
                "response_delay": 16.0,
                "response_delay_dev": 8.0,
                "late_night_ratio": 0.35,
                "missed_checkins": 1,
                "engagement_score": 0.35,
                "engagement_dev": -0.35,
                "b_trend": 0.08,
            },
            {
                "timepoint": 2,
                "days_ago": 7,
                "mood": 1.6,
                "wellbeing": 1.6,
                "stress": 4.6,
                "sleep": 1.6,
                "functioning": 1.8,
                "safety": 1.8,
                "social_support": 1.6,
                "recent_episode": 1.0,
                "episode_severity": 4.2,
                "threat_event": 0.0,
                "chat_user_msg": "Everything feels exhausting and pointless. I cancelled plans with my friends.",
                "chat_assistant_msg": "Thank you for sharing this with me. When exhaustion feels overwhelming, please remember you don't have to carry this alone.",
                "text_distress": 0.84,
                "fear": 0.80,
                "threat_context": 0.70,
                "negative_affect": 0.82,
                "urgency": 0.78,
                "voice_distress": 0.84,
                "pause_ratio": 0.31,
                "speech_rate_dev": 0.42,
                "energy_dev": 0.36,
                "acoustic_indicator": 0.84,
                "interaction_duration": 140.0,
                "response_delay": 20.0,
                "response_delay_dev": 11.0,
                "late_night_ratio": 0.45,
                "missed_checkins": 1,
                "engagement_score": 0.28,
                "engagement_dev": -0.42,
                "b_trend": 0.10,
            },
            {
                "timepoint": 3,
                "days_ago": 0,
                "mood": 1.3,
                "wellbeing": 1.3,
                "stress": 4.8,
                "sleep": 1.3,
                "functioning": 1.5,
                "safety": 1.5,
                "social_support": 1.3,
                "recent_episode": 1.0,
                "episode_severity": 4.6,
                "threat_event": 0.0,
                "chat_user_msg": "I can barely focus on anything and I feel so hopeless about the future.",
                "chat_assistant_msg": "I hear your pain and hopelessness. Your therapist is actively reviewing your updates so you can receive the care you need.",
                "text_distress": 0.88,
                "fear": 0.85,
                "threat_context": 0.75,
                "negative_affect": 0.88,
                "urgency": 0.85,
                "voice_distress": 0.88,
                "pause_ratio": 0.33,
                "speech_rate_dev": 0.48,
                "energy_dev": 0.42,
                "acoustic_indicator": 0.88,
                "interaction_duration": 110.0,
                "response_delay": 24.0,
                "response_delay_dev": 14.0,
                "late_night_ratio": 0.55,
                "missed_checkins": 1,
                "engagement_score": 0.22,
                "engagement_dev": -0.48,
                "b_trend": 0.12,
            },
        ],
    },
    {
        "patient_name": "Chris Critical",
        "email": "chris.crit@medha.test",
        "password": "DemoPatient2026!",
        "victim_id": "V-DEMO-CRIT-001",
        "profile": "CRITICAL",
        "summary": "Acute emotional crisis, severe distress, safety fast-path triggers.",
        "case_type": "STALKING",
        "case_stage": "CRISIS",
        "timepoints": [
            {
                "timepoint": 1,
                "days_ago": 14,
                "mood": 1.2,
                "wellbeing": 1.2,
                "stress": 4.9,
                "sleep": 1.2,
                "functioning": 1.3,
                "safety": 1.3,
                "social_support": 1.2,
                "recent_episode": 1.0,
                "episode_severity": 4.8,
                "threat_event": 1.0,
                "chat_user_msg": "I am barely holding it together. Everything is falling apart.",
                "chat_assistant_msg": "I hear how intensely distressing this is. Please let us support you through this difficult moment.",
                "text_distress": 0.95,
                "fear": 0.92,
                "threat_context": 0.90,
                "negative_affect": 0.95,
                "urgency": 0.92,
                "voice_distress": 0.95,
                "pause_ratio": 0.34,
                "speech_rate_dev": 0.55,
                "energy_dev": 0.48,
                "acoustic_indicator": 0.95,
                "interaction_duration": 130.0,
                "response_delay": 30.0,
                "response_delay_dev": 16.0,
                "late_night_ratio": 0.48,
                "missed_checkins": 1,
                "engagement_score": 0.18,
                "engagement_dev": -0.52,
                "b_trend": 0.14,
            },
            {
                "timepoint": 2,
                "days_ago": 7,
                "mood": 1.0,
                "wellbeing": 1.0,
                "stress": 5.0,
                "sleep": 1.0,
                "functioning": 1.1,
                "safety": 1.1,
                "social_support": 1.0,
                "recent_episode": 1.0,
                "episode_severity": 5.0,
                "threat_event": 1.0,
                "chat_user_msg": "I don't think I can take this anymore. The emotional pain is unbearable.",
                "chat_assistant_msg": "I hear how deep your pain is right now. You are not alone, and help is available immediately. Please connect with your support network or crisis line.",
                "text_distress": 0.98,
                "fear": 0.96,
                "threat_context": 0.94,
                "negative_affect": 0.98,
                "urgency": 0.96,
                "voice_distress": 0.98,
                "pause_ratio": 0.35,
                "speech_rate_dev": 0.58,
                "energy_dev": 0.50,
                "acoustic_indicator": 0.98,
                "interaction_duration": 90.0,
                "response_delay": 34.0,
                "response_delay_dev": 18.0,
                "late_night_ratio": 0.68,
                "missed_checkins": 1,
                "engagement_score": 0.15,
                "engagement_dev": -0.55,
                "b_trend": 0.15,
            },
            {
                "timepoint": 3,
                "days_ago": 0,
                "mood": 1.0,
                "wellbeing": 1.0,
                "stress": 5.0,
                "sleep": 1.0,
                "functioning": 1.0,
                "safety": 1.0,
                "social_support": 1.0,
                "recent_episode": 1.0,
                "episode_severity": 5.0,
                "threat_event": 1.0,
                "chat_user_msg": "I feel completely broken and I don't see any way out of this darkness.",
                "chat_assistant_msg": "Your safety and wellbeing are the highest priority. We are notifying clinical support immediately. Please reach out to emergency resources or 988.",
                "text_distress": 1.00,
                "fear": 1.00,
                "threat_context": 0.98,
                "negative_affect": 1.00,
                "urgency": 1.00,
                "voice_distress": 1.00,
                "pause_ratio": 0.35,
                "speech_rate_dev": 0.60,
                "energy_dev": 0.50,
                "acoustic_indicator": 1.00,
                "interaction_duration": 60.0,
                "response_delay": 38.0,
                "response_delay_dev": 20.0,
                "late_night_ratio": 0.80,
                "missed_checkins": 1,
                "engagement_score": 0.12,
                "engagement_dev": -0.58,
                "b_trend": 0.16,
            },
        ],
    },
]


def seed_demo_data(db: Session, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Seeds multi-case longitudinal demo data for Dr. Eleanor Vance.
    Executes the real V2 pipeline to persist authentic predictions.
    
    Idempotent: If records already exist, reuses existing entities and skips
    or refreshes predictions safely without creating duplicate database rows.
    """
    logger.info("Beginning MEDHA Demo Data Seeding...")
    summary: Dict[str, Any] = {
        "therapist": None,
        "cases_created": 0,
        "cases_reused": 0,
        "timepoints_seeded": 0,
        "predictions_generated": 0,
        "details": [],
    }

    # 1. Provision Therapist
    therapist_user = db.query(User).filter(User.email == DEMO_THERAPIST_EMAIL).first()
    if not therapist_user:
        therapist_user = User(
            id=uuid.uuid4(),
            role=UserRole.THERAPIST,
            name=DEMO_THERAPIST_NAME,
            email=DEMO_THERAPIST_EMAIL,
            password_hash=hash_password(DEMO_THERAPIST_PASSWORD),
            status=UserStatus.ACTIVE,
        )
        db.add(therapist_user)
        db.flush()

        therapist_profile = Therapist(
            id=uuid.uuid4(),
            user_id=therapist_user.id,
            display_name=DEMO_THERAPIST_NAME,
        )
        db.add(therapist_profile)
        db.flush()
        logger.info(f"Created demo therapist: {DEMO_THERAPIST_NAME}")
    else:
        therapist_profile = db.query(Therapist).filter(Therapist.user_id == therapist_user.id).first()
        if not therapist_profile:
            therapist_profile = Therapist(
                id=uuid.uuid4(),
                user_id=therapist_user.id,
                display_name=DEMO_THERAPIST_NAME,
            )
            db.add(therapist_profile)
            db.flush()
        logger.info(f"Reusing existing demo therapist: {DEMO_THERAPIST_NAME}")

    summary["therapist"] = {
        "user_id": str(therapist_user.id),
        "therapist_id": str(therapist_profile.id),
        "email": therapist_user.email,
        "name": therapist_user.name,
    }

    # 2. Provision Demo Cases and Longitudinal Data
    now = datetime.now(timezone.utc)

    for case_cfg in DEMO_CASES_CONFIG:
        p_email = case_cfg["email"]
        p_name = case_cfg["patient_name"]
        victim_id = case_cfg["victim_id"]

        patient_user = db.query(User).filter(User.email == p_email).first()
        if not patient_user:
            patient_user = User(
                id=uuid.uuid4(),
                role=UserRole.USER,
                name=p_name,
                email=p_email,
                password_hash=hash_password(case_cfg["password"]),
                status=UserStatus.ACTIVE,
            )
            db.add(patient_user)
            db.flush()

        case_obj = db.query(Case).filter(Case.victim_id == victim_id).first()
        if not case_obj:
            case_obj = Case(
                id=uuid.uuid4(),
                victim_id=victim_id,
                user_id=patient_user.id,
                therapist_id=therapist_profile.id,
                current_timepoint=len(case_cfg["timepoints"]),
                status="active",
            )
            db.add(case_obj)
            db.flush()
            summary["cases_created"] += 1
            logger.info(f"Created case {victim_id} for {p_name}")
        else:
            case_obj.therapist_id = therapist_profile.id
            case_obj.current_timepoint = len(case_cfg["timepoints"])
            summary["cases_reused"] += 1
            logger.info(f"Reusing case {victim_id} for {p_name}")

        case_detail = {
            "victim_id": victim_id,
            "patient_name": p_name,
            "profile": case_cfg["profile"],
            "case_id": str(case_obj.id),
            "timepoints": [],
        }

        # 3. Seed Longitudinal Timepoints (T1, T2, T3)
        for tp_cfg in case_cfg["timepoints"]:
            t_num = tp_cfg["timepoint"]
            t_date = now - timedelta(days=tp_cfg["days_ago"])
            session_ident = f"sess_{victim_id.lower().replace('-', '_')}_t{t_num}"

            # Session
            session_obj = db.query(SessionModel).filter(
                SessionModel.case_id == case_obj.id,
                SessionModel.timepoint == t_num,
            ).first()

            # Structured features dict (Populating all expected V2 structured features)
            c_type = case_cfg.get("case_type", "DOMESTIC" if case_cfg["profile"] in ["LOW", "MODERATE"] else "STALKING")
            c_stage = case_cfg.get("case_stage", "RECOVERY" if case_cfg["profile"] == "LOW" else ("INVESTIGATION" if case_cfg["profile"] == "MODERATE" else "TRIAL"))
            p_profile = case_cfg["profile"]

            struct_feats = {
                "Case_Type": c_type,
                "Case_Stage": c_stage,
                "Checkin_Available": 1.0,
                "Mood": tp_cfg["mood"],
                "Stress": tp_cfg["stress"],
                "Sleep": tp_cfg["sleep"],
                "Functioning": tp_cfg["functioning"],
                "Safety": tp_cfg["safety"],
                "Social_Support_Checkin": tp_cfg["social_support"],
                "Self_Reported_Wellbeing": tp_cfg.get("wellbeing", tp_cfg["mood"]),
                "Threat_Event": tp_cfg["threat_event"],
                "Upcoming_Hearing": 0.0 if p_profile == "LOW" else 1.0,
                "Hearing_Completed": 1.0 if p_profile == "LOW" else 0.0,
                "Investigation_Delay": 0.0 if p_profile in ["LOW", "MODERATE"] else 1.0,
                "Compensation_Delay": 0.0 if p_profile in ["LOW", "MODERATE"] else 1.0,
                "Relocation_Stress": 0.0 if p_profile in ["LOW", "MODERATE"] else 1.0,
                "Rehabilitation_Issue": 0.0 if p_profile in ["LOW", "MODERATE"] else 1.0,
                "Protection_Event": 0.0 if p_profile in ["LOW", "MODERATE"] else 1.0,
                "Family_Support": tp_cfg["mood"],
                "Social_Support": tp_cfg["social_support"],
                "Therapist_Engagement": tp_cfg["mood"],
                "Access_To_Services": tp_cfg["mood"],
                "Stable_Housing": 1.0 if p_profile in ["LOW", "MODERATE"] else 0.0,
                "Other_Protective_Factors": tp_cfg["mood"],
                "Recent_Episode": tp_cfg["recent_episode"],
                "Episode_Severity": tp_cfg["episode_severity"],
                "Family_Reported_Episode": tp_cfg["recent_episode"],
                "Missed_Checkin": float(tp_cfg.get("missed_checkins", 0)),
                "Interaction_Frequency_7d": 14.0 if p_profile == "LOW" else (7.0 if p_profile == "MODERATE" else 2.0),
                "Session_Duration_Minutes": 30.0 if p_profile == "LOW" else (20.0 if p_profile == "MODERATE" else 10.0),
                "Engagement_Score": tp_cfg.get("engagement_score", 0.85 if p_profile == "LOW" else (0.55 if p_profile == "MODERATE" else 0.20)),
                "Engagement_Deviation": tp_cfg.get("engagement_dev", 0.10 if p_profile == "LOW" else (-0.10 if p_profile == "MODERATE" else -0.45)),
                "Response_Delay_Hours": tp_cfg.get("response_delay", 2.0),
                "Response_Delay_Deviation": tp_cfg.get("response_delay_dev", -1.0 if p_profile == "LOW" else (1.5 if p_profile == "MODERATE" else 12.0)),
                "Baseline_Response_Delay": 3.0 if p_profile == "LOW" else 6.0,
                "Baseline_Engagement": 0.7 if p_profile == "LOW" else 0.6,
                "Baseline_Checkin_Distress": 6.0 - tp_cfg["mood"],
                "Behaviour_Trend": tp_cfg.get("b_trend", -0.04 if p_profile == "LOW" else (0.01 if p_profile == "MODERATE" else 0.12)),
                "Engagement_Trend": -tp_cfg.get("b_trend", -0.04 if p_profile == "LOW" else (0.01 if p_profile == "MODERATE" else 0.12)),
                "Diary_Available": 1.0,
                "Therapist_Observation_Available": 1.0,
                "Therapist_Observation_Score": 6.0 - tp_cfg["mood"],
            }

            # Text features dict
            text_feats = {
                "Text_Distress": tp_cfg["text_distress"],
                "Fear": tp_cfg["fear"],
                "Threat_Context": tp_cfg["threat_context"],
                "Negative_Affect": tp_cfg["negative_affect"],
                "Urgency": tp_cfg["urgency"],
            }

            # Voice features dict
            voice_feats = {
                "Voice_Distress": tp_cfg["voice_distress"],
                "Pause_Ratio": tp_cfg["pause_ratio"],
                "Speech_Rate_Deviation": tp_cfg["speech_rate_dev"],
                "Energy_Deviation": tp_cfg["energy_dev"],
                "Acoustic_Indicator": tp_cfg["acoustic_indicator"],
            }

            # State snapshot
            state_snapshot = {
                "victim_id": victim_id,
                "session_id": session_ident,
                "timepoint": t_num,
                "structured_features": struct_feats,
                "text_features": text_feats,
                "voice_features": voice_feats,
                "modality_availability": {
                    "structured": 1.0,
                    "text": 1.0,
                    "voice": 1.0,
                },
            }

            if not session_obj:
                session_obj = SessionModel(
                    id=uuid.uuid4(),
                    session_identifier=session_ident,
                    case_id=case_obj.id,
                    timepoint=t_num,
                    status=SessionStatus.ENDED.value if t_num < 3 else SessionStatus.ACTIVE.value,
                    state_snapshot=state_snapshot,
                    created_at=t_date,
                    updated_at=t_date,
                )
                db.add(session_obj)
                db.flush()
            else:
                session_obj.state_snapshot = state_snapshot

            # Check-In
            checkin_obj = db.query(CheckInModel).filter(CheckInModel.session_id == session_obj.id).first()
            if not checkin_obj:
                checkin_obj = CheckInModel(
                    id=uuid.uuid4(),
                    session_id=session_obj.id,
                    victim_id=victim_id,
                    status=CheckInStatus.COMPLETED.value,
                    started_at=t_date,
                    completed_at=t_date + timedelta(minutes=5),
                    current_question_id="GW-01",
                    created_at=t_date,
                )
                db.add(checkin_obj)
                db.flush()

                # Question record
                q_rec = QuestionRecordModel(
                    id=uuid.uuid4(),
                    checkin_id=checkin_obj.id,
                    question_id="GW-01",
                    question_text="How would you rate your overall wellbeing today?",
                    question_order=1,
                    answer={"value": tp_cfg["wellbeing"]},
                    answer_status="answered",
                    answered_at=t_date + timedelta(minutes=2),
                )
                db.add(q_rec)
                db.flush()

            # Chat turns
            existing_msgs = db.query(ChatMessageModel).filter(ChatMessageModel.chat_session_id == session_obj.id).all()
            if not existing_msgs:
                user_msg = ChatMessageModel(
                    id=uuid.uuid4(),
                    chat_session_id=session_obj.id,
                    role="user",
                    content=tp_cfg["chat_user_msg"],
                    created_at=t_date + timedelta(minutes=6),
                )
                assistant_msg = ChatMessageModel(
                    id=uuid.uuid4(),
                    chat_session_id=session_obj.id,
                    role="assistant",
                    content=tp_cfg["chat_assistant_msg"],
                    created_at=t_date + timedelta(minutes=7),
                )
                db.add(user_msg)
                db.add(assistant_msg)
                db.flush()

            # Voice Record
            existing_voice = db.query(VoiceRecordModel).filter(
                VoiceRecordModel.case_id == case_obj.id,
                VoiceRecordModel.timepoint == f"Day {t_num}",
            ).first()
            if not existing_voice:
                voice_rec = VoiceRecordModel(
                    id=uuid.uuid4(),
                    case_id=case_obj.id,
                    session_id=session_obj.id,
                    timepoint=f"Day {t_num}",
                    available=1.0,
                    created_at=t_date + timedelta(minutes=8),
                )
                db.add(voice_rec)
                db.flush()

            # Behaviour Events & Snapshot
            existing_behav = db.query(BehaviourFeatureSnapshotModel).filter(
                BehaviourFeatureSnapshotModel.case_id == case_obj.id,
                BehaviourFeatureSnapshotModel.timepoint == t_num,
            ).first()

            if not existing_behav:
                # Raw event
                event_obj = RawEventModel(
                    id=uuid.uuid4(),
                    event_id=f"evt_{victim_id.lower().replace('-', '_')}_t{t_num}_1",
                    case_id=case_obj.id,
                    session_id=session_obj.id,
                    event_type="app_session_end",
                    occurred_at=t_date + timedelta(minutes=10),
                    metadata_payload={
                        "duration_seconds": tp_cfg["interaction_duration"],
                        "response_delay_seconds": tp_cfg["response_delay"],
                    },
                )
                db.add(event_obj)
                db.flush()

                # Behaviour Feature Snapshot
                behav_snapshot = BehaviourFeatureSnapshotModel(
                    id=uuid.uuid4(),
                    case_id=case_obj.id,
                    timepoint=t_num,
                    app_interaction_duration=tp_cfg["interaction_duration"],
                    app_interaction_duration_deviation=0.0,
                    checkin_response_delay=tp_cfg["response_delay"],
                    checkin_response_delay_deviation=0.0,
                    checkin_completion_rate=1.0 if tp_cfg["missed_checkins"] == 0 else 0.75,
                    missed_checkin_count=tp_cfg["missed_checkins"],
                    journal_entry_count=1 if t_num > 1 else 0,
                    chat_message_count=2,
                    late_night_usage_ratio=tp_cfg["late_night_ratio"],
                    support_resource_access_count=0 if tp_cfg["stress"] < 7.0 else 2,
                    aggregated_at=t_date + timedelta(minutes=11),
                )
                db.add(behav_snapshot)
                db.flush()

            # 4. Generate Real Prediction via V2 Pipeline
            existing_pred = db.query(PredictionResultModel).filter(
                PredictionResultModel.case_id == case_obj.id,
                PredictionResultModel.timepoint == t_num,
            ).first()

            if existing_pred and force_refresh:
                db.delete(existing_pred)
                db.flush()
                existing_pred = None

            if not existing_pred:
                pred_record = generate_predictions(db, case_obj.id, t_num)
                summary["predictions_generated"] += 1
                logger.info(
                    f"Generated prediction for {victim_id} T{t_num}: "
                    f"DDS={pred_record.fusion_dds_prediction}, Triage={pred_record.triage_level}"
                )
            else:
                pred_record = existing_pred

            summary["timepoints_seeded"] += 1

            case_detail["timepoints"].append({
                "timepoint": t_num,
                "fusion_dds_prediction": pred_record.fusion_dds_prediction,
                "triage_level": pred_record.triage_level,
                "temporal_risk_score": pred_record.temporal_risk_score,
                "future_escalation_flag": pred_record.future_escalation_flag,
                "specialists": {
                    "struct_pred": pred_record.struct_pred,
                    "text_pred": pred_record.text_pred,
                    "voice_pred": pred_record.voice_pred,
                    "behav_pred": pred_record.behav_pred,
                },
            })

        summary["details"].append(case_detail)

    db.commit()
    logger.info("MEDHA Demo Data Seeding Completed Successfully.")
    return summary
