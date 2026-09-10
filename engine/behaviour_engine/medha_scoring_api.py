"""
MEDHA Behaviour Scoring API.

Serves the frozen Isolation Forest + formulas from medha_scoring_artifacts.joblib
as a microservice. One patient, one day at a time -- this is stage 4 ("Frozen
model scoring") from the real-time pipeline discussed earlier. It is NOT the
GRU/fusion model itself: it produces the 3-vector (+ a ready-to-feed sequence)
that a separate fusion orchestrator consumes alongside the NLP/voice services.

Run:  uvicorn app:app --reload --port 8000
"""
import os
from collections import defaultdict, deque
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ARTIFACTS_PATH = os.environ.get("MEDHA_ARTIFACTS_PATH", "/home/claude/build3/medha_scoring_artifacts.joblib")
SEQ_WINDOW = 30  # matches the GRU tensor shape agreed earlier: (candidates, 30, 3)

PURE_FEATURES = ["completion_baseline_z", "latency_baseline_z", "question_skip_rate"]
Z_COLS = ["completion_baseline_z", "latency_baseline_z",
          "session_duration_baseline_z", "response_length_baseline_z"]

app = FastAPI(title="MEDHA Behaviour Scoring API", version="1.0")

# ---------------------------------------------------------------------
# Frozen artifacts, loaded once at process startup -- not per request.
# ---------------------------------------------------------------------
_artifacts = {}
# Per-patient rolling state. In-memory dict is fine for a hackathon
# prototype / single-process demo; swap for Redis or a DB table keyed by
# patient_id before running multiple workers or surviving a restart.
_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=SEQ_WINDOW))


@app.on_event("startup")
def load_artifacts():
    art = joblib.load(ARTIFACTS_PATH)
    _artifacts["imputer"] = art["imputer"]
    _artifacts["scaler"] = art["scaler"]
    _artifacts["iso_forest"] = art["iso_forest"]
    _artifacts["reference_raw_scores"] = art["reference_raw_scores"]


def anomaly_percentile(raw_score: float) -> float:
    ref = _artifacts["reference_raw_scores"]
    return float(np.searchsorted(ref, raw_score, side="left") / len(ref))


# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------
class DailyFeaturesIn(BaseModel):
    day_index: int
    completion_baseline_z: Optional[float] = None
    latency_baseline_z: Optional[float] = None
    question_skip_rate: Optional[float] = None
    session_duration_baseline_z: Optional[float] = None
    response_length_baseline_z: Optional[float] = None
    missed_checkins: int = Field(default=0, ge=0)


class ScoreOut(BaseModel):
    patient_id: str
    day_index: int
    anomaly_score: Optional[float]
    engagement_deviation: Optional[float]
    inactivity_score: float
    behavioral_risk_score: Optional[float]
    triage_status: str
    insufficient_history: bool
    gru_sequence: list[list[float]]       # [anomaly, engagement, inactivity] per stored day, 0.0 where invalid
    gru_sequence_mask: list[bool]          # True = real observation, False = insufficient-history placeholder


# ---------------------------------------------------------------------
# Core scoring -- same math as the batch pipeline, one row at a time
# ---------------------------------------------------------------------
def score_one_day(patient_id: str, f: DailyFeaturesIn) -> ScoreOut:
    pure_vals = pd.DataFrame([[getattr(f, c) if getattr(f, c) is not None else np.nan
                                for c in PURE_FEATURES]], columns=PURE_FEATURES)
    have_any = not bool(pure_vals.isna().all(axis=None))

    anomaly_score = None
    if have_any:
        X = _artifacts["scaler"].transform(_artifacts["imputer"].transform(pure_vals))
        raw = float(-_artifacts["iso_forest"].decision_function(X)[0])
        anomaly_score = anomaly_percentile(raw)

    z_vals = [getattr(f, c) for c in Z_COLS if getattr(f, c) is not None]
    engagement_deviation = float(np.mean(np.abs(z_vals))) if z_vals else None

    hist = _history[patient_id]
    hist.append({"missed": f.missed_checkins, "anomaly": anomaly_score,
                  "engagement": engagement_deviation, "valid": have_any})
    recent_missed = [h["missed"] for h in list(hist)[-3:]]
    inactivity_score = float(np.mean(recent_missed))

    if have_any:
        eng_contrib = float(np.clip((engagement_deviation or 0.0) / 3.0, 0, 1))
        risk = 0.4 * anomaly_score + 0.3 * eng_contrib + 0.3 * inactivity_score
        if risk < 0.25:
            triage = "GREEN -- Monitor"
        elif risk < 0.50:
            triage = "YELLOW -- Observe"
        elif risk < 0.75:
            triage = "ORANGE -- Human Review"
        else:
            triage = "RED -- Urgent Escalation"
    else:
        risk, triage = None, "GRAY -- Insufficient History"

    gru_sequence = [[h["anomaly"] or 0.0, h["engagement"] or 0.0,
                      float(np.mean([hh["missed"] for hh in list(hist)[max(0, i - 2):i + 1]])) ]
                     for i, h in enumerate(hist)]
    gru_mask = [h["valid"] for h in hist]

    return ScoreOut(
        patient_id=patient_id, day_index=f.day_index,
        anomaly_score=anomaly_score, engagement_deviation=engagement_deviation,
        inactivity_score=inactivity_score, behavioral_risk_score=risk,
        triage_status=triage, insufficient_history=not have_any,
        gru_sequence=gru_sequence, gru_sequence_mask=gru_mask,
    )


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "artifacts_loaded": bool(_artifacts)}


@app.post("/v1/patients/{patient_id}/score", response_model=ScoreOut)
def score_patient_day(patient_id: str, payload: DailyFeaturesIn):
    if not _artifacts:
        raise HTTPException(503, "Model artifacts not loaded")
    return score_one_day(patient_id, payload)


@app.get("/v1/patients/{patient_id}/sequence")
def get_sequence(patient_id: str):
    hist = _history.get(patient_id)
    if not hist:
        raise HTTPException(404, "No history for this patient yet")
    return {
        "patient_id": patient_id,
        "n_days": len(hist),
        "gru_sequence": [[h["anomaly"] or 0.0, h["engagement"] or 0.0, 0.0] for h in hist],
        "gru_sequence_mask": [h["valid"] for h in hist],
    }
