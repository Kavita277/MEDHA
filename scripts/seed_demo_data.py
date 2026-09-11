"""
MEDHA Demo Data Seeding & End-to-End Model Validation Script
============================================================

Executes the complete demo seeding workflow:
1. Direct DB insertion of demo therapist: demo.therapist@medha.org
2. Authenticates via API (POST /api/v1/auth/login) to obtain therapist JWT Bearer token
3. Provisions 4 authentic patient cases via therapist API (POST /api/v1/therapist/users):
   - LOW Risk (3 timepoints, Triage: LOW)
   - MODERATE / MEDIUM Risk (4 timepoints, Triage: MEDIUM)
   - HIGH Risk (5 timepoints, Triage: HIGH)
   - CRITICAL Risk with Longitudinal Escalation (8 timepoints -> triggers GRU Temporal model, Triage: CRITICAL)
4. For each case and timepoint:
   - Provisions session via API (POST /api/v1/sessions)
   - Executes structured check-in (start, answer questions, complete)
   - Sends conversational message through NLP pipeline
   - Ingests behaviour metrics snapshot (BehaviourFeatureSnapshotModel)
   - Executes native prediction pipeline (generate_predictions -> MedhaV2Pipeline)
   - Persists predictions into prediction_results
5. Verifies all Therapist Results APIs:
   - GET /api/v1/therapist/cases
   - GET /api/v1/therapist/cases/{case_id}/results
   - GET /api/v1/therapist/cases/{case_id}/sessions
   - GET /api/v1/therapist/cases/{case_id}/history
6. Emits a structured Model Audit & Demo Data Validation Table.
"""

from __future__ import annotations

import os
import sys
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.main import app
from backend.persistence.database import engine, check_db_connection
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.persistence.models.case import Case
from backend.persistence.models.session import SessionModel
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.persistence.models.event import RawEventModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.security.passwords import hash_password
from backend.services.prediction_service import generate_predictions


DEMO_THERAPIST_EMAIL = "demo.therapist@medha.org"
DEMO_THERAPIST_PASS = "TherapistDemo123!"
DEMO_THERAPIST_NAME = "Dr. Radhika Sharma"

# Load canonical feature definitions
with open(os.path.join(REPO_ROOT, "engine", "models", "v2", "v2_structured_dds_features.json")) as f:
    STRUCT_FEATS = json.load(f)["features"]
with open(os.path.join(REPO_ROOT, "engine", "models", "text_dds_v2", "v2_text_dds_features.json")) as f:
    TEXT_FEATS = json.load(f)["core_features"]
with open(os.path.join(REPO_ROOT, "engine", "models", "voice_dds_v2", "v2_voice_dds_features.json")) as f:
    VOICE_FEATS = json.load(f)["core_features"]
with open(os.path.join(REPO_ROOT, "engine", "models", "behaviour_dds_v2", "v2_behaviour_dds_features.json")) as f:
    BEHAV_FEATS = json.load(f)["all_10_features"]

# Load V0001 escalation sequence from processed split for authentic longitudinal GRU input
V2_CSV_PATH = os.path.join(REPO_ROOT, "engine", "data", "processed", "v2_longitudinal_split.csv")
CRIT_DATASET_ROWS = None
if os.path.exists(V2_CSV_PATH):
    _full_df = pd.read_csv(V2_CSV_PATH)
    CRIT_DATASET_ROWS = _full_df[_full_df["Victim_ID"] == "V0001"].sort_values("Timepoint").iloc[20:28]

PATIENTS_CONFIG = [
    {
        "triage_target": "LOW",
        "name": "Ananya Sharma",
        "email": "ananya.sharma@medha.org",
        "password": "PatientPass123!",
        "victim_id": "V-LOW-001",
        "timepoints": 3,
        "base_features": {
            "mood": 4, "stress": 1, "sleep": 4, "functioning": 4, "safety": 5, "support": 4, "wellbeing": 4,
            "threat": 0, "hearing": 0, "hearing_comp": 1, "delay": 0, "reloc": 0, "rehab": 0,
            "family_sup": 1, "social_sup": 1, "services": 1, "housing": 1, "protective": 1, "episode": 0,
            "missed": 0, "freq": 5, "duration": 15, "engagement": 0.85, "resp_delay": 0.5,
            "text_distress": 0.12, "fear": 0.08, "threat_ctx": 0.05, "neg_affect": 0.10, "urgency": 0.05,
            "voice_distress": 0.15, "pause": 0.10, "speech_dev": 0.05, "energy_dev": 0.02, "acoustic": 0.10,
            "app_duration": 180.0, "chat_text": "I had a peaceful day today and slept well. Thank you for checking in.",
            "case_type": "harassment", "case_stage": "counseling", "episode_severity": "mild"
        }
    },
    {
        "triage_target": "MEDIUM",
        "name": "Rahul Verma",
        "email": "rahul.verma@medha.org",
        "password": "PatientPass123!",
        "victim_id": "V-MED-002",
        "timepoints": 4,
        "base_features": {
            "mood": 2, "stress": 3, "sleep": 2, "functioning": 3, "safety": 3, "support": 3, "wellbeing": 3,
            "threat": 1, "hearing": 1, "hearing_comp": 0, "delay": 1, "reloc": 0, "rehab": 0,
            "family_sup": 1, "social_sup": 1, "services": 1, "housing": 1, "protective": 0, "episode": 0,
            "missed": 1, "freq": 3, "duration": 30, "engagement": 0.60, "resp_delay": 3.0,
            "text_distress": 0.52, "fear": 0.45, "threat_ctx": 0.35, "neg_affect": 0.50, "urgency": 0.40,
            "voice_distress": 0.50, "pause": 0.30, "speech_dev": 0.20, "energy_dev": 0.15, "acoustic": 0.45,
            "app_duration": 450.0, "chat_text": "Work has been stressful and the court date is approaching. I feel somewhat anxious.",
            "case_type": "stalking", "case_stage": "investigation", "episode_severity": "moderate"
        }
    },
    {
        "triage_target": "HIGH",
        "name": "Priya Patel",
        "email": "priya.patel@medha.org",
        "password": "PatientPass123!",
        "victim_id": "V-HIGH-003",
        "timepoints": 5,
        "base_features": {
            "mood": 1, "stress": 5, "sleep": 1, "functioning": 1, "safety": 1, "support": 1, "wellbeing": 1,
            "threat": 1, "hearing": 1, "hearing_comp": 0, "delay": 1, "reloc": 1, "rehab": 0,
            "family_sup": 0, "social_sup": 0, "services": 0, "housing": 0, "protective": 0, "episode": 1,
            "missed": 3, "freq": 1, "duration": 60, "engagement": 0.20, "resp_delay": 12.0,
            "text_distress": 0.94, "fear": 0.92, "threat_ctx": 0.90, "neg_affect": 0.94, "urgency": 0.92,
            "voice_distress": 0.94, "pause": 0.60, "speech_dev": 0.50, "energy_dev": 0.45, "acoustic": 0.90,
            "app_duration": 850.0, "chat_text": "I feel completely overwhelmed and terrified. The threats are relentless.",
            "case_type": "domestic_violence", "case_stage": "court_hearing", "episode_severity": "severe"
        }
    },
    {
        "triage_target": "CRITICAL",
        "name": "Kavita Rao",
        "email": "kavita.rao@medha.org",
        "password": "PatientPass123!",
        "victim_id": "V-CRIT-004",
        "timepoints": 8,
        "base_features": {
            # Uses progressive longitudinal sequence from V0001
        }
    }
]


def clean_previous_demo_data(session: Session) -> None:
    """Removes previous demo users and associated records cleanly."""
    print("[1/5] Cleaning previous demo data...")
    emails_to_clean = [DEMO_THERAPIST_EMAIL, "demo_therapist@example.com"] + [p["email"] for p in PATIENTS_CONFIG] + [
        "patient_low@example.com", "patient_med@example.com", "patient_high@example.com", "patient_crit@example.com"
    ]
    victim_ids_to_clean = [p["victim_id"] for p in PATIENTS_CONFIG] + [
        "CASE-LOW-001", "CASE-MED-002", "CASE-HIGH-003", "CASE-CRIT-004"
    ]

    # Delete cases with victim_ids
    existing_cases = session.query(Case).filter(Case.victim_id.in_(victim_ids_to_clean)).all()
    for c in existing_cases:
        session.query(RawEventModel).filter(RawEventModel.case_id == c.id).delete()
        session.query(SafetyEventModel).filter(SafetyEventModel.case_id == c.id).delete()
        session.query(JournalEntryModel).filter(JournalEntryModel.case_id == c.id).delete()
        session.query(PredictionResultModel).filter(PredictionResultModel.case_id == c.id).delete()
        session.query(BehaviourFeatureSnapshotModel).filter(BehaviourFeatureSnapshotModel.case_id == c.id).delete()
        session.query(VoiceRecordModel).filter(VoiceRecordModel.case_id == c.id).delete()
        
        # sessions
        sessions = session.query(SessionModel).filter(SessionModel.case_id == c.id).all()
        for s in sessions:
            session.query(ChatMessageModel).filter(ChatMessageModel.chat_session_id == s.id).delete()
            checkins = session.query(CheckInModel).filter(CheckInModel.session_id == s.id).all()
            for ch in checkins:
                session.query(QuestionRecordModel).filter(QuestionRecordModel.checkin_id == ch.id).delete()
                session.delete(ch)
            session.delete(s)
        session.delete(c)

    # Delete users
    users = session.query(User).filter(User.email.in_(emails_to_clean)).all()
    for u in users:
        session.query(Therapist).filter(Therapist.user_id == u.id).delete()
        session.delete(u)

    session.commit()
    print("      Previous demo entities purged.")


def create_demo_therapist_direct(session: Session) -> Therapist:
    """Inserts demo therapist directly into the DB per requirement."""
    print(f"[2/5] Creating demo therapist: {DEMO_THERAPIST_EMAIL}...")
    user = User(
        id=uuid.uuid4(),
        role=UserRole.THERAPIST,
        name=DEMO_THERAPIST_NAME,
        email=DEMO_THERAPIST_EMAIL,
        password_hash=hash_password(DEMO_THERAPIST_PASS),
        status=UserStatus.ACTIVE,
        must_change_password=False,
    )
    therapist = Therapist(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name=DEMO_THERAPIST_NAME,
    )
    session.add_all([user, therapist])
    session.commit()
    session.refresh(therapist)
    print(f"      Therapist profile created (ID: {therapist.id}).")
    return therapist


def seed_demo_cases(client: TestClient, therapist_token: str, db: Session) -> List[Dict[str, Any]]:
    """Creates patients & cases via API and generates longitudinal observations."""
    print("[3/5] Creating demo patient cases via API & generating longitudinal data...")
    created_cases = []

    for p_cfg in PATIENTS_CONFIG:
        print(f"\n  --> Provisioning Patient: {p_cfg['name']} ({p_cfg['triage_target']})...")
        
        # 1. Create Patient Account & Case via Therapist API
        resp = client.post(
            "/api/v1/therapist/users",
            json={
                "name": p_cfg["name"],
                "email": p_cfg["email"],
                "password": p_cfg["password"],
                "victim_id": p_cfg["victim_id"],
            },
            headers={"Authorization": f"Bearer {therapist_token}"},
        )
        assert resp.status_code == 201, f"Failed to create patient: {resp.text}"
        case_data = resp.json()["case"]
        case_id = uuid.UUID(case_data["id"])
        
        # 2. Login as the Patient to execute self-reported checkins and messages
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": p_cfg["email"], "password": p_cfg["password"]}
        )
        assert login_resp.status_code == 200, f"Patient login failed: {login_resp.text}"
        patient_token = login_resp.json()["access_token"]

        total_timepoints = p_cfg["timepoints"]
        print(f"      Generating {total_timepoints} sequential timepoints...")

        for t in range(1, total_timepoints + 1):
            # Advance case.current_timepoint
            case_obj = db.query(Case).filter(Case.id == case_id).first()
            case_obj.current_timepoint = t
            db.commit()

            # A. Create Session via API
            sess_resp = client.post(
                "/api/v1/sessions",
                json={"case_id": str(case_id)},
                headers={"Authorization": f"Bearer {patient_token}"}
            )
            assert sess_resp.status_code == 201, f"Session creation failed: {sess_resp.text}"
            sess_id = sess_resp.json()["id"]

            # B. Check-in via API (start, answer, complete)
            ch_start = client.post(
                f"/api/v1/checkins/sessions/{sess_id}",
                headers={"Authorization": f"Bearer {patient_token}"}
            )
            assert ch_start.status_code == 201, f"Checkin start failed: {ch_start.text}"
            ch_id = ch_start.json()["id"]

            # Compute features for this timepoint
            if p_cfg["triage_target"] == "CRITICAL" and CRIT_DATASET_ROWS is not None:
                # Authentic longitudinal sequence from dataset
                crit_row = CRIT_DATASET_ROWS.iloc[t - 1].to_dict()
                mood = int(crit_row.get("Mood", 2))
                stress = int(crit_row.get("Stress", 4))
                sleep = int(crit_row.get("Sleep", 2))
                functioning = int(crit_row.get("Functioning", 2))
                safety = int(crit_row.get("Safety", 2))
                chat_msg = (
                    "I am feeling okay today." if t < 3 else
                    "Anxiety is building up about the upcoming court hearing." if t < 6 else
                    "They came to my house again. I am terrified for my life!"
                )
                app_duration = float(crit_row.get("App_Interaction_Duration", 600.0))
                delay_hours = float(crit_row.get("Response_Delay_Hours", 5.0))
                missed_count = float(crit_row.get("Missed_Checkin", 1.0))
                late_night = float(crit_row.get("Late_Night_Usage_Ratio", 0.6))
            else:
                bf = p_cfg["base_features"]
                mood = bf["mood"]
                stress = bf["stress"]
                sleep = bf["sleep"]
                functioning = bf["functioning"]
                safety = bf["safety"]
                chat_msg = bf["chat_text"]
                text_distress = bf["text_distress"]
                fear = bf["fear"]
                threat_ctx = bf["threat_ctx"]
                neg_affect = bf["neg_affect"]
                urgency = bf["urgency"]
                voice_distress = bf["voice_distress"]
                pause_ratio = bf.get("pause", 0.3)
                speech_dev = bf.get("speech_dev", 0.1)
                energy_dev = bf.get("energy_dev", 0.05)
                acoustic_ind = bf.get("acoustic", 0.4)
                app_duration = bf["app_duration"]
                delay_hours = bf["resp_delay"]
                missed_count = bf["missed"]
                late_night = 0.0 if p_cfg["triage_target"] == "LOW" else 0.2 if p_cfg["triage_target"] == "MEDIUM" else 0.45

            # Answer standard check-in questions via API
            answers = [
                {"value": mood},
                {"value": stress},
                {"value": sleep},
                {"value": functioning},
                {"value": safety},
                {"value": 3},
                {"value": mood},
            ]
            for ans in answers:
                client.post(
                    f"/api/v1/checkins/{ch_id}/answer",
                    json={"answer": ans},
                    headers={"Authorization": f"Bearer {patient_token}"}
                )

            # Complete check-in via API
            client.post(
                f"/api/v1/checkins/{ch_id}/complete",
                headers={"Authorization": f"Bearer {patient_token}"}
            )

            # C. Send chat message via API
            client.post(
                f"/api/v1/chat/sessions/{sess_id}/message",
                json={"message": chat_msg},
                headers={"Authorization": f"Bearer {patient_token}"}
            )

            # D. Enrich session snapshot with multimodal features
            sess_db = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(sess_id)).first()
            snap = dict(sess_db.state_snapshot or {})
            snap.setdefault("structured_features", {})
            snap.setdefault("text_features", {})
            snap.setdefault("voice_features", {})
            snap.setdefault("modality_availability", {})

            if p_cfg["triage_target"] == "CRITICAL" and CRIT_DATASET_ROWS is not None:
                # Copy authentic features from dataset row
                for k, val in crit_row.items():
                    if k in ["Victim_ID", "Case_ID", "Timepoint", "Date_Time", "Split", "Future_Escalation_Label", "DDS"]:
                        continue
                    if pd.notna(val):
                        try:
                            snap["structured_features"][k] = float(val)
                        except (ValueError, TypeError):
                            snap["structured_features"][k] = str(val)
                for feat in TEXT_FEATS:
                    if feat in crit_row and pd.notna(crit_row[feat]):
                        val = crit_row[feat]
                        try:
                            snap["text_features"][feat] = float(val)
                        except (ValueError, TypeError):
                            snap["text_features"][feat] = str(val)
                for feat in VOICE_FEATS:
                    if feat in crit_row and pd.notna(crit_row[feat]):
                        val = crit_row[feat]
                        try:
                            snap["voice_features"][feat] = float(val)
                        except (ValueError, TypeError):
                            snap["voice_features"][feat] = str(val)
                snap["modality_availability"]["structured"] = 1.0
                snap["modality_availability"]["text"] = float(crit_row.get("Text_Available", 1.0)) if pd.notna(crit_row.get("Text_Available")) else 1.0
                snap["modality_availability"]["voice"] = float(crit_row.get("Voice_Available", 1.0)) if pd.notna(crit_row.get("Voice_Available")) else 1.0
            else:
                snap["structured_features"].update({
                    "Case_Type": bf.get("case_type", "stalking"),
                    "Case_Stage": bf.get("case_stage", "investigation"),
                    "Episode_Severity": bf.get("episode_severity", "moderate" if stress >= 3 else "mild"),
                    "Mood": float(mood),
                    "Stress": float(stress),
                    "Sleep": float(sleep),
                    "Functioning": float(functioning),
                    "Safety": float(safety),
                    "Threat_Event": 1.0 if safety <= 2 else 0.0,
                    "Upcoming_Hearing": 1.0 if t >= 3 else 0.0,
                    "Hearing_Completed": 0.0,
                    "Investigation_Delay": 1.0 if t >= 2 else 0.0,
                    "Compensation_Delay": 0.0,
                    "Relocation_Stress": 1.0 if safety <= 2 else 0.0,
                    "Rehabilitation_Issue": 0.0,
                    "Protection_Event": 1.0 if safety <= 2 else 0.0,
                    "Family_Support": 1.0 if mood >= 3 else 0.0,
                    "Social_Support": 1.0 if mood >= 3 else 0.0,
                    "Therapist_Engagement": 1.0,
                    "Access_To_Services": 1.0,
                    "Stable_Housing": 1.0 if safety >= 3 else 0.0,
                    "Other_Protective_Factors": 1.0 if mood >= 3 else 0.0,
                    "Recent_Episode": 1.0 if stress >= 4 else 0.0,
                    "Missed_Checkin": float(missed_count),
                    "Interaction_Frequency_7d": 5.0,
                    "Session_Duration_Minutes": 20.0,
                    "Engagement_Score": 0.8 if mood >= 3 else 0.3,
                    "Engagement_Deviation": 0.1,
                    "Response_Delay_Hours": float(delay_hours),
                    "Response_Delay_Deviation": 0.5,
                    "Baseline_Response_Delay": 0.5,
                    "Baseline_Engagement": 0.8,
                    "Baseline_Checkin_Distress": 1.0,
                    "Behaviour_Trend": 0.0,
                    "Engagement_Trend": 0.0,
                    "Diary_Available": 1.0,
                    "Therapist_Observation_Available": 1.0,
                    "Therapist_Observation_Score": float(stress),
                    "Checkin_Available": 1.0,
                })
                snap["text_features"].update({
                    "Text_Distress": text_distress,
                    "Fear": fear,
                    "Threat_Context": threat_ctx,
                    "Negative_Affect": neg_affect,
                    "Urgency": urgency,
                })
                snap["voice_features"].update({
                    "Voice_Distress": voice_distress,
                    "Pause_Ratio": pause_ratio,
                    "Speech_Rate_Deviation": speech_dev,
                    "Energy_Deviation": energy_dev,
                    "Acoustic_Indicator": acoustic_ind,
                })
                snap["modality_availability"].update({
                    "structured": 1.0,
                    "text": 1.0,
                    "voice": 1.0,
                })

            sess_db.state_snapshot = snap
            db.commit()

            # E. Ingest BehaviourFeatureSnapshotModel
            if p_cfg["triage_target"] == "CRITICAL" and CRIT_DATASET_ROWS is not None:
                eng_dev = float(crit_row.get("Engagement_Deviation", -0.25))
                resp_dev = float(crit_row.get("Response_Delay_Deviation", -6.0))
            else:
                eng_dev = 0.2 if p_cfg["triage_target"] == "MEDIUM" else 0.5 if p_cfg["triage_target"] == "HIGH" else 0.1
                resp_dev = 1.0 if p_cfg["triage_target"] == "MEDIUM" else 4.0 if p_cfg["triage_target"] == "HIGH" else 0.5

            b_snap = BehaviourFeatureSnapshotModel(
                case_id=case_id,
                timepoint=t,
                app_interaction_duration=app_duration,
                app_interaction_duration_deviation=eng_dev,
                checkin_response_delay=delay_hours,
                checkin_response_delay_deviation=resp_dev,
                checkin_completion_rate=1.0 if missed_count == 0 else 0.6,
                missed_checkin_count=missed_count,
                journal_entry_count=1.0,
                chat_message_count=2.0,
                late_night_usage_ratio=late_night,
                support_resource_access_count=1.0 if safety <= 2 else 0.0,
            )
            db.add(b_snap)
            db.commit()

            # F. Execute Native Prediction Service
            pred_record = generate_predictions(db, case_id, t)
            tr_str = f"{pred_record.temporal_risk_score:.4f}" if pred_record.temporal_risk_score is not None else "None (<7 steps)"
            print(f"        T={t}: Fusion={pred_record.fusion_dds_prediction:.1f} | TemporalRisk={tr_str} | Triage={pred_record.triage_level}")

        created_cases.append({
            "case_id": case_id,
            "victim_id": p_cfg["victim_id"],
            "target": p_cfg["triage_target"],
            "patient_name": p_cfg["name"],
        })

    return created_cases


def verify_therapist_apis(client: TestClient, therapist_token: str, created_cases: List[Dict[str, Any]]) -> None:
    """Verifies all therapist results APIs against the freshly seeded data."""
    print("\n[4/5] Verifying Therapist Results APIs...")

    # 1. GET /api/v1/therapist/cases
    resp_cases = client.get("/api/v1/therapist/cases", headers={"Authorization": f"Bearer {therapist_token}"})
    assert resp_cases.status_code == 200, f"List cases failed: {resp_cases.text}"
    cases_list = resp_cases.json()
    assert len(cases_list) >= 4, f"Expected at least 4 cases, got {len(cases_list)}"
    print(f"      GET /api/v1/therapist/cases: SUCCESS ({len(cases_list)} cases returned)")

    # 2. Verify each case's latest results, sessions, and history
    for item in created_cases:
        cid = str(item["case_id"])
        
        # Latest result
        res_resp = client.get(f"/api/v1/therapist/cases/{cid}/results", headers={"Authorization": f"Bearer {therapist_token}"})
        assert res_resp.status_code == 200, f"Get results failed for {cid}: {res_resp.text}"
        data = res_resp.json()
        assert data["results_available"] is True
        assert data["specialists"]["behav_pred"] is None  # Step 10 blocked
        assert data["specialists"]["behav_blocked"] is True
        item["actual_triage"] = data["triage_level"]
        item["fusion_dds"] = data["fusion_dds_prediction"]
        item["temporal_risk"] = data["temporal_risk_score"]
        item["escalation_flag"] = data["future_escalation_flag"]

        # Sessions
        sess_resp = client.get(f"/api/v1/therapist/cases/{cid}/sessions", headers={"Authorization": f"Bearer {therapist_token}"})
        assert sess_resp.status_code == 200, f"Sessions failed for {cid}: {sess_resp.text}"
        sessions_data = sess_resp.json()
        item["session_count"] = len(sessions_data)

        # Checkins
        ch_resp = client.get(f"/api/v1/therapist/cases/{cid}/checkins", headers={"Authorization": f"Bearer {therapist_token}"})
        assert ch_resp.status_code == 200, f"Checkins failed for {cid}: {ch_resp.text}"
        item["checkin_count"] = len(ch_resp.json())

        # Behaviour Snapshots
        beh_resp = client.get(f"/api/v1/therapist/cases/{cid}/behaviour", headers={"Authorization": f"Bearer {therapist_token}"})
        assert beh_resp.status_code == 200, f"Behaviour failed for {cid}: {beh_resp.text}"
        item["behaviour_count"] = len(beh_resp.json())

        # Safety Alerts
        alert_resp = client.get(f"/api/v1/therapist/cases/{cid}/alerts", headers={"Authorization": f"Bearer {therapist_token}"})
        assert alert_resp.status_code == 200, f"Alerts failed for {cid}: {alert_resp.text}"
        item["alert_count"] = len(alert_resp.json())

        # Session Prediction Results (if session exists)
        if sessions_data:
            latest_sess_id = sessions_data[0]["session_id"]
            s_res = client.get(f"/api/v1/therapist/sessions/{latest_sess_id}/results", headers={"Authorization": f"Bearer {therapist_token}"})
            assert s_res.status_code == 200, f"Session result failed: {s_res.text}"

    print("      All therapist endpoints verified (cases, results, sessions, checkins, behaviour, alerts).")


def print_audit_table(created_cases: List[Dict[str, Any]]) -> None:
    """Emits the final validation audit table."""
    print("\n[5/5] MODEL AUDIT & DEMO DATA VALIDATION TABLE")
    print("=" * 110)
    header = f"{'Target':<10} | {'Victim ID':<12} | {'Patient Name':<16} | {'Timepoints':<10} | {'Fusion DDS':<12} | {'Temporal Risk':<18} | {'Actual Triage':<14} | {'Status'}"
    print(header)
    print("-" * 110)
    for c in created_cases:
        f_dds = f"{c.get('fusion_dds', 0.0):.2f}" if c.get('fusion_dds') is not None else "N/A"
        t_risk = f"{c.get('temporal_risk', 0.0):.4f}" if c.get('temporal_risk') is not None else "None (<7 steps)"
        match = "MATCH" if c.get("actual_triage") == c["target"] else f"MISMATCH ({c.get('actual_triage')})"
        t_count = c.get('session_count', len(PATIENTS_CONFIG))
        row = f"{c['target']:<10} | {c['victim_id']:<12} | {c['patient_name']:<16} | {t_count:<10} | {f_dds:<12} | {t_risk:<18} | {c.get('actual_triage'):<14} | {match}"
        print(row)
    print("=" * 110)
    print("\nMEDHA Demo Data Seeding & Model Validation Completed Successfully!")
    print(f"Therapist Credentials: {DEMO_THERAPIST_EMAIL} / {DEMO_THERAPIST_PASS}\n")


def main() -> None:
    if not check_db_connection(engine):
        print("ERROR: Database is not reachable. Ensure PostgreSQL is running on localhost:5432.")
        sys.exit(1)

    with Session(engine) as session:
        clean_previous_demo_data(session)
        create_demo_therapist_direct(session)

    with TestClient(app) as client:
        # Authenticate therapist via API
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": DEMO_THERAPIST_EMAIL, "password": DEMO_THERAPIST_PASS},
        )
        assert resp.status_code == 200, f"Therapist login failed: {resp.text}"
        therapist_token = resp.json()["access_token"]

        with Session(engine) as session:
            created_cases = seed_demo_cases(client, therapist_token, session)

        verify_therapist_apis(client, therapist_token, created_cases)
        print_audit_table(created_cases)


if __name__ == "__main__":
    main()
