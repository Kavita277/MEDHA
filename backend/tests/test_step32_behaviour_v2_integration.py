"""
MEDHA Backend Step 32 — Behaviour/V2 Integration Tests
=====================================================

Authoritative specification: backend/docs/backend_plan.md §32

Tests all 8 mandatory integration scenarios:
1. RAW EVENTS → BEHAVIOUR → SPECIALIST → FUSION
2. DUPLICATE EVENTS (Idempotency and Non-Inflation)
3. MISSING MODALITY (Graceful Fallback & Contract Adherence)
4. MISSING STRUCTURED FEATURES (Preprocessor Imputation)
5. MISSING VOICE (Unavailable Voice Handling)
6. INSUFFICIENT GRU HISTORY (T1–T7 Boundary Condition)
7. VALID SEVEN-TIMESTEP HISTORY (T8 First Eligible Temporal Prediction)
8. MULTIPLE TIMEPOINTS (T1 → T2 → T3 Longitudinal Isolation & Baselining)
+ CONTRACT DISCREPANCY TEST (T1 Cold-Start None-Deviation abs() Limitation)

Uses the REAL frozen V2 pipeline (MedhaV2Pipeline, XGBoost specialists, PyTorch GRU),
not mocks, and does not alter production or engine code.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from backend.integrations.medha_v2 import get_v2_pipeline, run_v2_inference
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.case import Case
from backend.persistence.models.event import RawEventModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.session import SessionModel
from backend.persistence.repositories.event import EventRepository
from backend.services.behaviour.feature_aggregator import BehaviourAggregatorService
from backend.services.prediction_service import generate_predictions
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline


# ============================================================================
# Helpers
# ============================================================================

def _make_base_structured_features(pipeline: MedhaV2Pipeline) -> Dict[str, Any]:
    """Returns a valid set of default structured features."""
    return {feat: 1.0 for feat in pipeline.structured_features}


def _make_base_text_features(pipeline: MedhaV2Pipeline) -> Dict[str, Any]:
    """Returns a valid set of default text features."""
    return {feat: 0.5 for feat in pipeline.text_features}


def _make_base_voice_features(pipeline: MedhaV2Pipeline) -> Dict[str, Any]:
    """Returns a valid set of default voice features."""
    return {feat: 0.5 for feat in pipeline.voice_features}


def _make_base_behaviour_features(pipeline: MedhaV2Pipeline) -> Dict[str, Any]:
    """Returns a valid set of default behaviour features."""
    return {feat: 2.0 for feat in pipeline.behaviour_features_all}


# ============================================================================
# Scenario 1: RAW EVENTS → BEHAVIOUR → SPECIALIST → FUSION
# ============================================================================

def test_scenario_1_raw_events_to_behaviour_to_specialist_to_fusion(
    db_session: Session,
    test_case: Case,
):
    """
    Real end-to-end integration test:
    raw events
    → persisted RawEventModel
    → BehaviourAggregatorService
    → BehaviourFeatureSnapshotModel
    → behaviour feature mapping
    → real Behaviour specialist (Ridge all-10)
    → real V2 fusion (XGBoost)

    Verifies persistence, aggregation, feature mapping, specialist execution,
    and valid fusion DDS output.
    Uses T1 prior baseline so T2 aggregator computes real deviations and feeds
    the real frozen V2 pipeline without mocks.
    """
    case_id = test_case.id
    base_time = datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc)
    pipeline = get_v2_pipeline()

    # 1. Establish T1 baseline snapshot in DB so T2 has baseline history
    t1_snapshot = BehaviourFeatureSnapshotModel(
        id=uuid.uuid4(),
        case_id=case_id,
        timepoint=1,
        app_interaction_duration=600.0,
        app_interaction_duration_deviation=0.0,
        checkin_response_delay=6.0,
        checkin_response_delay_deviation=0.0,
        checkin_completion_rate=1.0,
        missed_checkin_count=0,
        journal_entry_count=1,
        chat_message_count=1,
        late_night_usage_ratio=0.0,
        support_resource_access_count=0,
    )
    db_session.add(t1_snapshot)
    db_session.commit()

    # 2. Ingest legitimate raw events for Timepoint 2
    t2_time = base_time + timedelta(days=1)
    raw_events = [
        RawEventModel(
            event_id=f"evt_start_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="session_start",
            occurred_at=t2_time,
            metadata_payload={},
        ),
        RawEventModel(
            event_id=f"evt_journal_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="journal_saved",
            occurred_at=t2_time + timedelta(minutes=2),
            metadata_payload={"journal_id": "journal_entry_001"},
        ),
        RawEventModel(
            event_id=f"evt_chat_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="chat_message_sent",
            occurred_at=t2_time + timedelta(minutes=4),
            metadata_payload={"role": "user", "message_id": "msg_001"},
        ),
        RawEventModel(
            event_id=f"evt_chk_prompt_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="checkin_prompt_shown",
            occurred_at=t2_time + timedelta(minutes=6),
            metadata_payload={},
        ),
        RawEventModel(
            event_id=f"evt_chk_start_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="checkin_started",
            occurred_at=t2_time + timedelta(minutes=6, seconds=2),
            metadata_payload={},
        ),
        RawEventModel(
            event_id=f"evt_chk_done_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="checkin_completed",
            occurred_at=t2_time + timedelta(minutes=6, seconds=14),
            metadata_payload={},
        ),
        RawEventModel(
            event_id=f"evt_support_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="support_resource_accessed",
            occurred_at=t2_time + timedelta(minutes=10),
            metadata_payload={"resource_id": "safety_plan"},
        ),
        RawEventModel(
            event_id=f"evt_end_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            event_type="session_end",
            occurred_at=t2_time + timedelta(minutes=15),
            metadata_payload={},
        ),
    ]

    # Persist events via EventRepository
    repo = EventRepository(db_session)
    inserted = repo.batch_insert_idempotent(raw_events)
    db_session.commit()
    assert inserted == len(raw_events)

    # Verify events are persisted in DB
    stored_count = db_session.query(RawEventModel).filter(RawEventModel.case_id == case_id).count()
    assert stored_count == len(raw_events)

    # 3. Also persist an active session with state snapshot (providing structured & text features)
    session_record = SessionModel(
        id=uuid.uuid4(),
        case_id=case_id,
        session_identifier=f"sess_{uuid.uuid4().hex[:8]}",
        timepoint=2,
        status="ACTIVE",
        state_snapshot={
            "structured_features": _make_base_structured_features(pipeline),
            "text_features": _make_base_text_features(pipeline),
            "voice_features": {},
            "modality_availability": {
                "structured": 1.0,
                "text": 1.0,
                "voice": 0.0,
            },
        },
    )
    db_session.add(session_record)
    db_session.commit()

    # 4. Run BehaviourAggregatorService
    aggregator = BehaviourAggregatorService(db_session)
    snapshot_dto = aggregator.aggregate_case_timepoint(case_id, timepoint=2)

    # Verify expected behaviour metrics
    assert snapshot_dto.app_interaction_duration == 900.0  # 15 min = 900s
    assert snapshot_dto.journal_entry_count == 1.0
    assert snapshot_dto.chat_message_count == 1.0
    assert snapshot_dto.checkin_completion_rate == 1.0
    assert snapshot_dto.checkin_response_delay == 14.0  # 14s from prompt to completed
    assert snapshot_dto.support_resource_access_count == 1.0
    # Deviation against T1 baseline (600.0 duration, 6.0 delay)
    assert snapshot_dto.app_interaction_duration_deviation == pytest.approx(900.0 - 600.0)  # +300.0
    assert snapshot_dto.checkin_response_delay_deviation == pytest.approx(14.0 - 6.0)       # +8.0

    # Verify BehaviourFeatureSnapshotModel was persisted
    db_snapshot = db_session.query(BehaviourFeatureSnapshotModel).filter_by(
        case_id=case_id, timepoint=2
    ).first()
    assert db_snapshot is not None
    assert db_snapshot.journal_entry_count == 1.0
    assert db_snapshot.chat_message_count == 1.0

    # 5. Generate predictions via real V2 pipeline
    prediction_record = generate_predictions(db_session, case_id, timepoint=2)

    # 6. Verify PredictionResultModel persistence and output validity
    assert prediction_record is not None
    assert prediction_record.case_id == case_id
    assert prediction_record.timepoint == 2

    # Specialist outputs
    assert prediction_record.struct_pred is not None
    assert isinstance(prediction_record.struct_pred, float)
    assert prediction_record.text_pred is not None
    assert isinstance(prediction_record.text_pred, float)
    assert prediction_record.behav_pred is not None
    assert isinstance(prediction_record.behav_pred, float)
    assert not math.isnan(prediction_record.behav_pred)

    # Voice was not available
    assert prediction_record.voice_available is False
    assert prediction_record.voice_pred is None

    # Real V2 Fusion DDS
    assert prediction_record.fusion_dds_prediction is not None
    assert 0.0 <= prediction_record.fusion_dds_prediction <= 100.0
    assert prediction_record.triage_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Verify persisted in database
    persisted_pred = db_session.query(PredictionResultModel).filter_by(
        case_id=case_id, timepoint=2
    ).first()
    assert persisted_pred is not None
    assert persisted_pred.id == prediction_record.id
    assert persisted_pred.fusion_dds_prediction == prediction_record.fusion_dds_prediction


# ============================================================================
# Scenario 2: DUPLICATE EVENTS
# ============================================================================

def test_scenario_2_duplicate_events_idempotency_and_stability(
    db_session: Session,
    test_case: Case,
):
    """
    Submits identical events with identical event_id values multiple times.
    Verifies:
    - repository ingestion remains idempotent (no error, ignores duplicate event_ids)
    - duplicate events do not increase database row counts
    - behaviour features are not inflated
    - downstream prediction is not distorted
    - resulting feature values and predictions match the single-event scenario
    """
    case_id = test_case.id
    base_time = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc)

    # Seed T1 baseline so T2 has baseline history for deviations
    t1_snapshot = BehaviourFeatureSnapshotModel(
        id=uuid.uuid4(),
        case_id=case_id,
        timepoint=1,
        app_interaction_duration=500.0,
        app_interaction_duration_deviation=0.0,
        checkin_response_delay=5.0,
        checkin_response_delay_deviation=0.0,
        checkin_completion_rate=1.0,
        missed_checkin_count=0,
        journal_entry_count=1,
        chat_message_count=1,
        late_night_usage_ratio=0.0,
        support_resource_access_count=0,
    )
    db_session.add(t1_snapshot)
    db_session.commit()

    def _create_events() -> List[RawEventModel]:
        return [
            RawEventModel(
                event_id="fixed_evt_journal_001",
                case_id=case_id,
                event_type="journal_saved",
                occurred_at=base_time,
                metadata_payload={"journal_id": "j_100"},
            ),
            RawEventModel(
                event_id="fixed_evt_chat_001",
                case_id=case_id,
                event_type="chat_message_sent",
                occurred_at=base_time + timedelta(minutes=5),
                metadata_payload={"role": "user"},
            ),
            RawEventModel(
                event_id="fixed_evt_chk_prompt_001",
                case_id=case_id,
                event_type="checkin_prompt_shown",
                occurred_at=base_time + timedelta(minutes=6),
                metadata_payload={},
            ),
            RawEventModel(
                event_id="fixed_evt_chk_done_001",
                case_id=case_id,
                event_type="checkin_completed",
                occurred_at=base_time + timedelta(minutes=6, seconds=10),
                metadata_payload={},
            ),
            RawEventModel(
                event_id="fixed_evt_session_start_001",
                case_id=case_id,
                event_type="session_start",
                occurred_at=base_time,
                metadata_payload={},
            ),
            RawEventModel(
                event_id="fixed_evt_session_end_001",
                case_id=case_id,
                event_type="session_end",
                occurred_at=base_time + timedelta(minutes=10),
                metadata_payload={},
            ),
        ]

    repo = EventRepository(db_session)

    # First ingestion
    first_batch = _create_events()
    first_inserted = repo.batch_insert_idempotent(first_batch)
    db_session.commit()
    assert first_inserted == 6

    count_after_first = db_session.query(RawEventModel).filter_by(case_id=case_id).count()
    assert count_after_first == 6

    # First aggregation and prediction at T2
    aggregator = BehaviourAggregatorService(db_session)
    first_snapshot = aggregator.aggregate_case_timepoint(case_id, timepoint=2)
    first_pred = generate_predictions(db_session, case_id, timepoint=2)

    first_journal_count = first_snapshot.journal_entry_count
    first_chat_count = first_snapshot.chat_message_count
    first_duration = first_snapshot.app_interaction_duration
    first_behav_pred = first_pred.behav_pred
    first_fusion_dds = first_pred.fusion_dds_prediction

    # Second ingestion with identical event_id values
    second_batch = _create_events()
    second_inserted = repo.batch_insert_idempotent(second_batch)
    db_session.commit()
    assert second_inserted == 0, "Duplicate event_ids must be ignored by batch_insert_idempotent"

    # Verify raw event count did not increase
    count_after_second = db_session.query(RawEventModel).filter_by(case_id=case_id).count()
    assert count_after_second == 6

    # Re-run aggregation
    second_snapshot = aggregator.aggregate_case_timepoint(case_id, timepoint=2)

    # Features must NOT be inflated
    assert second_snapshot.journal_entry_count == first_journal_count == 1.0
    assert second_snapshot.chat_message_count == first_chat_count == 1.0
    assert second_snapshot.app_interaction_duration == first_duration == 600.0

    # Re-run prediction
    # Remove previous prediction record so generate_predictions can re-insert cleanly
    db_session.query(PredictionResultModel).filter_by(case_id=case_id, timepoint=2).delete()
    db_session.commit()

    second_pred = generate_predictions(db_session, case_id, timepoint=2)

    # Predictions must not be distorted
    assert second_pred.behav_pred == pytest.approx(first_behav_pred, rel=1e-5)
    assert second_pred.fusion_dds_prediction == pytest.approx(first_fusion_dds, rel=1e-5)


# ============================================================================
# Scenario 3: MISSING MODALITY
# ============================================================================

def test_scenario_3_missing_modality_graceful_fallback(
    test_case: Case,
):
    """
    Tests the real V2 pipeline with missing modalities (text missing, voice missing,
    or both missing) according to its actual input contract.
    Verifies:
    - unavailable modalities have 0 availability flags
    - corresponding specialist predictions are None
    - fusion executes successfully under missing modality flags
    - resulting DDS is valid and no exception occurs
    """
    pipeline = get_v2_pipeline()

    # Case A: Text missing, Voice missing, Structured + Behaviour available
    features_a = {
        **_make_base_structured_features(pipeline),
        **_make_base_behaviour_features(pipeline),
        "Struct_Available": 1.0,
        "Text_Available": 0.0,
        "Voice_Available": 0.0,
        "Behav_Available": 1.0,
    }
    preds_a = run_v2_inference(test_case.victim_id, 1, features_a)

    assert preds_a["Text_Pred"] is None
    assert preds_a["Voice_Pred"] is None
    assert preds_a["Struct_Pred"] is not None
    assert preds_a["Behav_Pred"] is not None
    assert preds_a["Fusion_DDS_Prediction"] is not None
    assert 0.0 <= preds_a["Fusion_DDS_Prediction"] <= 100.0

    # Case B: Voice missing, Text available, Structured available, Behaviour missing
    features_b = {
        **_make_base_structured_features(pipeline),
        **_make_base_text_features(pipeline),
        "Struct_Available": 1.0,
        "Text_Available": 1.0,
        "Voice_Available": 0.0,
        "Behav_Available": 0.0,
    }
    preds_b = run_v2_inference(test_case.victim_id, 1, features_b)

    assert preds_b["Voice_Pred"] is None
    assert preds_b["Text_Pred"] is not None
    assert preds_b["Struct_Pred"] is not None
    assert preds_b["Fusion_DDS_Prediction"] is not None
    assert 0.0 <= preds_b["Fusion_DDS_Prediction"] <= 100.0

    # Case C: All specialists missing except structured
    features_c = {
        **_make_base_structured_features(pipeline),
        "Struct_Available": 1.0,
        "Text_Available": 0.0,
        "Voice_Available": 0.0,
        "Behav_Available": 0.0,
    }
    preds_c = run_v2_inference(test_case.victim_id, 1, features_c)

    assert preds_c["Text_Pred"] is None
    assert preds_c["Voice_Pred"] is None
    assert preds_c["Struct_Pred"] is not None
    assert preds_c["Fusion_DDS_Prediction"] is not None
    assert 0.0 <= preds_c["Fusion_DDS_Prediction"] <= 100.0


# ============================================================================
# Scenario 4: MISSING STRUCTURED FEATURES
# ============================================================================

def test_scenario_4_missing_structured_features_imputation(
    test_case: Case,
):
    """
    Provides an incomplete structured feature set.
    Specifically tests omission of:
    - Missed_Checkin
    - Upcoming_Hearing
    - Investigation_Delay

    Verifies:
    - missing values are imputed by the existing SimpleImputer in struct_preproc
    - Struct_Pred is produced without error
    - Fusion prediction completes and produces a valid DDS score
    """
    pipeline = get_v2_pipeline()

    # Create full structured features, then omit the required 3 columns
    struct_features = _make_base_structured_features(pipeline)
    omitted_features = ["Missed_Checkin", "Upcoming_Hearing", "Investigation_Delay"]

    for feat in omitted_features:
        assert feat in pipeline.structured_features, f"{feat} must be in pipeline.structured_features"
        del struct_features[feat]

    # Also verify they are genuinely absent from the input dictionary
    for feat in omitted_features:
        assert feat not in struct_features

    features = {
        **struct_features,
        **_make_base_text_features(pipeline),
        **_make_base_behaviour_features(pipeline),
        "Struct_Available": 1.0,
        "Text_Available": 1.0,
        "Voice_Available": 0.0,
        "Behav_Available": 1.0,
    }

    # Run inference through real V2 pipeline
    preds = run_v2_inference(test_case.victim_id, 1, features)

    # Struct_Pred must be successfully generated despite missing features
    assert preds["Struct_Pred"] is not None
    assert isinstance(preds["Struct_Pred"], float)
    assert 0.0 <= preds["Struct_Pred"] <= 100.0

    # Fusion prediction must succeed
    assert preds["Fusion_DDS_Prediction"] is not None
    assert isinstance(preds["Fusion_DDS_Prediction"], float)
    assert 0.0 <= preds["Fusion_DDS_Prediction"] <= 100.0


# ============================================================================
# Scenario 5: MISSING VOICE
# ============================================================================

def test_scenario_5_missing_voice_inference(
    test_case: Case,
):
    """
    Runs inference with legitimate structured, text, and behaviour inputs
    but NO voice data.
    Verifies:
    - Voice_Available reflects unavailable voice (0 or False)
    - Voice_Pred is None
    - Fusion completes successfully
    - Fusion_DDS_Prediction is valid
    """
    pipeline = get_v2_pipeline()

    features = {
        **_make_base_structured_features(pipeline),
        **_make_base_text_features(pipeline),
        **_make_base_behaviour_features(pipeline),
        "Struct_Available": 1.0,
        "Text_Available": 1.0,
        "Voice_Available": 0.0,
        "Behav_Available": 1.0,
    }

    # Explicitly do NOT provide any voice features
    for voice_col in pipeline.voice_features:
        assert voice_col not in features

    preds = run_v2_inference(test_case.victim_id, 1, features)

    # Voice_Pred must be None when Voice_Available == 0
    assert preds["Voice_Pred"] is None

    # Other specialists must be valid
    assert preds["Struct_Pred"] is not None
    assert preds["Text_Pred"] is not None
    assert preds["Behav_Pred"] is not None

    # Fusion DDS prediction must be valid
    assert preds["Fusion_DDS_Prediction"] is not None
    assert 0.0 <= preds["Fusion_DDS_Prediction"] <= 100.0


# ============================================================================
# Scenario 6: INSUFFICIENT GRU HISTORY
# ============================================================================

def test_scenario_6_insufficient_gru_history_boundary():
    """
    Explicitly tests the frozen GRU history contract.
    The frozen implementation requires SEVEN PREVIOUS rows before the current
    row can receive temporal inference.

    Verifies:
    - rows 0 through 6 (timesteps T1 through T7) have < 7 preceding timesteps
    - Temporal_Available == 0 on those rows
    - Temporal_Risk_Score is NaN (or None)
    - Future_Escalation_Flag is NaN (or None)
    - T7 has only 6 preceding rows and is NOT eligible for temporal prediction
    """
    pipeline = get_v2_pipeline()
    victim_id = "V-GRU-INSUFF-001"

    # Construct a sequence of exactly 7 timesteps (T1 to T7)
    rows = []
    for t in range(1, 8):
        row = {
            "Victim_ID": victim_id,
            "Timepoint": t,
            **_make_base_structured_features(pipeline),
            **_make_base_text_features(pipeline),
            **_make_base_voice_features(pipeline),
            **_make_base_behaviour_features(pipeline),
            "Struct_Available": 1.0,
            "Text_Available": 1.0,
            "Voice_Available": 1.0,
            "Behav_Available": 1.0,
        }
        # Ensure all GRU features are present
        for gf in pipeline.gru_features:
            if gf not in row:
                row[gf] = 0.0
        rows.append(row)

    df = pd.DataFrame(rows)
    result_df = pipeline.predict_v2(df)

    assert len(result_df) == 7

    # Verify EVERY row from T1 to T7 has NO temporal inference
    for i in range(7):
        row_i = result_df.iloc[i]
        tp = row_i["Timepoint"]
        assert row_i["Temporal_Available"] == 0, f"Row {i} (T{tp}) must have Temporal_Available == 0"
        assert pd.isna(row_i["Temporal_Risk_Score"]), f"Row {i} (T{tp}) must have NaN Temporal_Risk_Score"
        assert pd.isna(row_i["Future_Escalation_Flag"]), f"Row {i} (T{tp}) must have NaN Future_Escalation_Flag"


# ============================================================================
# Scenario 7: VALID SEVEN-TIMESTEP HISTORY
# ============================================================================

def test_scenario_7_valid_seven_timestep_history_gru_inference():
    """
    Constructs a longitudinal dataframe with at least 8 sequential timesteps
    for the SAME Victim_ID.

    The first seven rows (T1–T7) provide history.
    The eighth row (T8) is the first row eligible for GRU inference.

    At T8 verifies:
    - Temporal_Available == 1
    - Temporal_Risk_Score is not None / not NaN
    - 0.0 <= Temporal_Risk_Score <= 1.0
    - Future_Escalation_Flag is either 0 or 1
    Uses the REAL frozen PyTorch GRU model.
    """
    pipeline = get_v2_pipeline()
    victim_id = "V-GRU-VALID-001"

    # Construct a sequence of 10 sequential timesteps (T1 to T10)
    rows = []
    for t in range(1, 11):
        row = {
            "Victim_ID": victim_id,
            "Timepoint": t,
            **_make_base_structured_features(pipeline),
            **_make_base_text_features(pipeline),
            **_make_base_voice_features(pipeline),
            **_make_base_behaviour_features(pipeline),
            "Struct_Available": 1.0,
            "Text_Available": 1.0,
            "Voice_Available": 1.0,
            "Behav_Available": 1.0,
        }
        for gf in pipeline.gru_features:
            if gf not in row:
                row[gf] = 0.1 * t
        rows.append(row)

    df = pd.DataFrame(rows)
    result_df = pipeline.predict_v2(df)

    assert len(result_df) == 10

    # Rows 0..6 (T1–T7) must have Temporal_Available == 0
    for i in range(7):
        assert result_df.iloc[i]["Temporal_Available"] == 0
        assert pd.isna(result_df.iloc[i]["Temporal_Risk_Score"])
        assert pd.isna(result_df.iloc[i]["Future_Escalation_Flag"])

    # Row 7 (T8) is the FIRST row eligible for GRU inference
    row_t8 = result_df.iloc[7]
    assert row_t8["Timepoint"] == 8
    assert row_t8["Temporal_Available"] == 1
    assert not pd.isna(row_t8["Temporal_Risk_Score"])
    assert 0.0 <= float(row_t8["Temporal_Risk_Score"]) <= 1.0
    assert row_t8["Future_Escalation_Flag"] in [0, 1]

    # Subsequent rows (T9, T10) are also eligible
    for i in [8, 9]:
        row_later = result_df.iloc[i]
        assert row_later["Temporal_Available"] == 1
        assert not pd.isna(row_later["Temporal_Risk_Score"])
        assert 0.0 <= float(row_later["Temporal_Risk_Score"]) <= 1.0
        assert row_later["Future_Escalation_Flag"] in [0, 1]


# ============================================================================
# Scenario 8: MULTIPLE TIMEPOINTS
# ============================================================================

def test_scenario_8_multiple_timepoints_isolation_and_baselines(
    db_session: Session,
    test_case: Case,
):
    """
    Creates sequential timepoints: T1 → T2 → T3.
    Verifies:
    - timepoints remain distinct in database
    - behavioural aggregation is associated with the correct timepoint
    - baseline/deviation calculations use only strictly prior observations
    - no future timepoint contaminates an earlier baseline
    - predictions are associated with the correct timepoint
    - longitudinal state is preserved
    """
    case_id = test_case.id
    base_time = datetime(2026, 9, 11, 8, 0, 0, tzinfo=timezone.utc)
    repo = EventRepository(db_session)
    aggregator = BehaviourAggregatorService(db_session)

    # -------------------------------------------------------------------------
    # TIMEPOINT 1
    # Duration = 100s, Delay = 5.0s
    # -------------------------------------------------------------------------
    t1_start = base_time
    t1_end = base_time + timedelta(hours=2)
    t1_events = [
        RawEventModel(
            event_id=f"t1_s_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_start",
            occurred_at=t1_start,
        ),
        RawEventModel(
            event_id=f"t1_e_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_end",
            occurred_at=t1_start + timedelta(seconds=100),
        ),
        RawEventModel(
            event_id=f"t1_p_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_prompt_shown",
            occurred_at=t1_start + timedelta(seconds=10),
        ),
        RawEventModel(
            event_id=f"t1_c_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_completed",
            occurred_at=t1_start + timedelta(seconds=15),
        ),
    ]
    repo.batch_insert_idempotent(t1_events)
    db_session.commit()

    s1 = aggregator.aggregate_case_timepoint(case_id, timepoint=1, start_time=t1_start, end_time=t1_end)
    assert s1.app_interaction_duration == 100.0
    assert s1.checkin_response_delay == 5.0
    # Cold start: strictly prior observations = 0 => deviations must be None
    assert s1.app_interaction_duration_deviation is None
    assert s1.checkin_response_delay_deviation is None

    # Step 30 pattern: for T1 prediction generation, initialize cold-start baseline deviation to 0.0
    # (as established in Step 30 seed service and test fixtures)
    s1_db = db_session.query(BehaviourFeatureSnapshotModel).filter_by(case_id=case_id, timepoint=1).first()
    s1_db.app_interaction_duration_deviation = 0.0
    s1_db.checkin_response_delay_deviation = 0.0
    db_session.commit()

    pred1 = generate_predictions(db_session, case_id, timepoint=1)
    assert pred1.timepoint == 1

    # -------------------------------------------------------------------------
    # TIMEPOINT 2
    # Duration = 200s, Delay = 15.0s
    # -------------------------------------------------------------------------
    t2_start = base_time + timedelta(days=1)
    t2_end = t2_start + timedelta(hours=2)
    t2_events = [
        RawEventModel(
            event_id=f"t2_s_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_start",
            occurred_at=t2_start,
        ),
        RawEventModel(
            event_id=f"t2_e_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_end",
            occurred_at=t2_start + timedelta(seconds=200),
        ),
        RawEventModel(
            event_id=f"t2_p_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_prompt_shown",
            occurred_at=t2_start + timedelta(seconds=10),
        ),
        RawEventModel(
            event_id=f"t2_c_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_completed",
            occurred_at=t2_start + timedelta(seconds=25),
        ),
    ]
    repo.batch_insert_idempotent(t2_events)
    db_session.commit()

    s2 = aggregator.aggregate_case_timepoint(case_id, timepoint=2, start_time=t2_start, end_time=t2_end)
    assert s2.app_interaction_duration == 200.0
    assert s2.checkin_response_delay == 15.0
    # Prior mean: [100.0] duration, [5.0] delay
    # Deviations = current - prior_mean
    assert s2.app_interaction_duration_deviation == pytest.approx(200.0 - 100.0)  # +100.0
    assert s2.checkin_response_delay_deviation == pytest.approx(15.0 - 5.0)       # +10.0

    pred2 = generate_predictions(db_session, case_id, timepoint=2)
    assert pred2.timepoint == 2

    # -------------------------------------------------------------------------
    # TIMEPOINT 3
    # Duration = 300s, Delay = 2.0s
    # -------------------------------------------------------------------------
    t3_start = base_time + timedelta(days=2)
    t3_end = t3_start + timedelta(hours=2)
    t3_events = [
        RawEventModel(
            event_id=f"t3_s_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_start",
            occurred_at=t3_start,
        ),
        RawEventModel(
            event_id=f"t3_e_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="session_end",
            occurred_at=t3_start + timedelta(seconds=300),
        ),
        RawEventModel(
            event_id=f"t3_p_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_prompt_shown",
            occurred_at=t3_start + timedelta(seconds=10),
        ),
        RawEventModel(
            event_id=f"t3_c_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            event_type="checkin_completed",
            occurred_at=t3_start + timedelta(seconds=12),
        ),
    ]
    repo.batch_insert_idempotent(t3_events)
    db_session.commit()

    s3 = aggregator.aggregate_case_timepoint(case_id, timepoint=3, start_time=t3_start, end_time=t3_end)
    assert s3.app_interaction_duration == 300.0
    assert s3.checkin_response_delay == 2.0
    # Prior mean from T1 and T2:
    # Duration prior mean = (100.0 + 200.0) / 2 = 150.0 => Dev = 300.0 - 150.0 = +150.0
    # Delay prior mean = (5.0 + 15.0) / 2 = 10.0 => Dev = 2.0 - 10.0 = -8.0
    assert s3.app_interaction_duration_deviation == pytest.approx(150.0)
    assert s3.checkin_response_delay_deviation == pytest.approx(-8.0)

    pred3 = generate_predictions(db_session, case_id, timepoint=3)
    assert pred3.timepoint == 3

    # -------------------------------------------------------------------------
    # VERIFY TIMEPOINT ISOLATION & NO CONTAMINATION
    # -------------------------------------------------------------------------
    # Check that 3 distinct snapshots and predictions exist
    snapshots = db_session.query(BehaviourFeatureSnapshotModel).filter_by(
        case_id=case_id
    ).order_by(BehaviourFeatureSnapshotModel.timepoint).all()
    assert len(snapshots) == 3
    assert [s.timepoint for s in snapshots] == [1, 2, 3]

    predictions = db_session.query(PredictionResultModel).filter_by(
        case_id=case_id
    ).order_by(PredictionResultModel.timepoint).all()
    assert len(predictions) == 3
    assert [p.timepoint for p in predictions] == [1, 2, 3]

    # Verify that temporal risk score is unavailable on per-timepoint check-ins
    # because per-timepoint inference does not have 7 prior rows in its single-row inference call
    for p in predictions:
        assert p.temporal_risk_score is None
        assert p.future_escalation_flag is None


# ============================================================================
# Regression / Contract Discrepancy Test
# ============================================================================

def test_frozen_v2_cold_start_none_deviation_limitation(
    db_session: Session,
    test_case: Case,
):
    """
    Exposes and verifies the frozen V2 pipeline contract discrepancy:
    At T1 cold start, BehaviourAggregatorService correctly produces None for deviations.
    When generate_predictions(case_id, 1) passes {'Engagement_Deviation': None}
    to MedhaV2Pipeline.predict_v2, the frozen pipeline executes:
        behav_df['Engagement_Deviation'] = behav_df['Engagement_Deviation'].abs()
    which raises TypeError on NoneType operands.

    This test verifies that:
    1. The aggregator strictly persists None for cold start (adhering to database/spec semantics)
    2. The frozen pipeline's behavior with None is faithfully documented and verified
    3. Production code is NOT altered to hide this limitation
    """
    case_id = test_case.id
    now = datetime(2026, 9, 11, 14, 0, 0, tzinfo=timezone.utc)
    repo = EventRepository(db_session)
    aggregator = BehaviourAggregatorService(db_session)

    # Ingest event for brand-new case at T1
    event = RawEventModel(
        event_id=f"cold_evt_{uuid.uuid4().hex[:6]}",
        case_id=case_id,
        event_type="session_start",
        occurred_at=now,
    )
    repo.batch_insert_idempotent([event])
    db_session.commit()

    # Cold-start aggregation produces None for deviation
    dto = aggregator.aggregate_case_timepoint(case_id, timepoint=1)
    assert dto.app_interaction_duration_deviation is None
    assert dto.checkin_response_delay_deviation is None

    # Verifies that calling generate_predictions directly on cold-start None deviation
    # exposes the frozen pipeline's TypeError without masking it
    with pytest.raises(TypeError, match="bad operand type for abs"):
        generate_predictions(db_session, case_id, timepoint=1)
