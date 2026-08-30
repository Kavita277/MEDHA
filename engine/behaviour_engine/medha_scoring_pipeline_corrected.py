"""
MEDHA Behaviour Engine -- corrected scoring pipeline.

Fixes vs. the previous draft (see chat for full rationale):
  1. No blind ffill leaking one candidate's score into another's early
     days. Missing pure_features are imputed per-row from a fitted
     training-median imputer; rows with NO usable feature at all are
     explicitly flagged "insufficient history", not silently zeroed.
  2. anomaly_score is percentile-ranked against a FROZEN training
     reference distribution, not batch min-max -- this is what makes
     single-patient real-time scoring actually work (see section 5).
  3. missed_checkins removed from the Isolation Forest feature set (it
     was held constant at scoring time by the old active-day filter and
     contributed nothing); inactivity_score is the dedicated feature for
     that signal.
  4. engagement_deviation averages only the z-columns actually observed
     that day (no more diluting toward 0 via fillna-before-mean).
  5. Evaluation runs on the FULL test set, not just missed_checkins==0
     rows -- triage has to cover missed check-ins, not exclude them.
  6. Stress tests call the real scoring function end-to-end; nothing is
     hardcoded.
  7. Model artifacts are persisted, and a genuine single-row real-time
     scoring demo is included.
"""
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (roc_auc_score, average_precision_score,
                              precision_score, recall_score, f1_score, confusion_matrix)

SEED = 42
DATA_PATH = "/mnt/user-data/outputs/MEDHA_Behaviour_Engine_FINAL_1000_Candidates_30_Days.csv"
OUT_DIR = "/home/claude/build3"

PURE_FEATURES = ["completion_baseline_z", "latency_baseline_z", "question_skip_rate"]
Z_COLS = ["completion_baseline_z", "latency_baseline_z",
          "session_duration_baseline_z", "response_length_baseline_z"]

# ---------------------------------------------------------------------
# 1. Load + candidate-level split
# ---------------------------------------------------------------------
df = pd.read_csv(DATA_PATH).sort_values(["user_id", "day_index"]).reset_index(drop=True)
all_users = np.asarray(df["user_id"].unique(), dtype=object)
train_users, test_users = train_test_split(all_users, test_size=0.3, random_state=SEED)
train_df = df[df.user_id.isin(train_users)].copy()
test_df = df[df.user_id.isin(test_users)].copy()

# ---------------------------------------------------------------------
# 2. Fit on the stabilized baseline window (days 1-10, no missed
#    check-ins) -- matches Master Doc S18.2's "baseline stabilization
#    period before alerting activates". Kept as originally designed.
# ---------------------------------------------------------------------
baseline_mask = (train_df.day_index <= 10) & (train_df.missed_checkins == 0)
train_baseline = train_df.loc[baseline_mask, PURE_FEATURES].dropna()

imputer = SimpleImputer(strategy="median").fit(train_baseline)
scaler = StandardScaler().fit(imputer.transform(train_baseline))
X_train_scaled = scaler.transform(imputer.transform(train_baseline))

iso_forest = IsolationForest(n_estimators=200, contamination=0.05, random_state=SEED, n_jobs=-1)
iso_forest.fit(X_train_scaled)

# frozen reference distribution -- every future score, including a
# single isolated patient, is percentile-ranked against THIS, not
# against whatever else happens to be in the current batch.
reference_raw_scores = np.sort(-iso_forest.decision_function(X_train_scaled))


def anomaly_percentile(raw_scores):
    return np.searchsorted(reference_raw_scores, raw_scores, side="left") / len(reference_raw_scores)


def score_dataframe(frame):
    """Compute all 3 scores + composite + triage tier. Used identically
    for the real test set, the stress tests, and single-row demos."""
    frame = frame.copy()

    have_any = frame[PURE_FEATURES].notna().any(axis=1)
    X = scaler.transform(imputer.transform(frame.loc[have_any, PURE_FEATURES]))
    raw = -iso_forest.decision_function(X)
    frame.loc[have_any, "anomaly_score"] = anomaly_percentile(raw)
    frame["insufficient_history"] = ~have_any

    present_z = [c for c in Z_COLS if c in frame.columns]
    frame["engagement_deviation"] = frame[present_z].abs().mean(axis=1, skipna=True)

    if "user_id" in frame.columns and frame["user_id"].nunique() > 1:
        frame["inactivity_score"] = frame.groupby("user_id")["missed_checkins"].transform(
            lambda s: s.rolling(3, min_periods=1).mean())
    else:
        frame["inactivity_score"] = frame["missed_checkins"].rolling(3, min_periods=1).mean()

    eng_contrib = np.clip(frame["engagement_deviation"].fillna(0) / 3.0, 0, 1)
    risk = 0.4 * frame["anomaly_score"].fillna(0) + 0.3 * eng_contrib + 0.3 * frame["inactivity_score"].fillna(0)
    frame["behavioral_risk_score"] = risk.where(~frame["insufficient_history"], np.nan)
    frame["triage_status"] = np.select(
        [frame["insufficient_history"],
         frame["behavioral_risk_score"] < 0.25,
         frame["behavioral_risk_score"] < 0.50,
         frame["behavioral_risk_score"] < 0.75],
        ["GRAY -- Insufficient History", "GREEN -- Monitor", "YELLOW -- Observe", "ORANGE -- Human Review"],
        default="RED -- Urgent Escalation",
    )
    return frame


test_df = score_dataframe(test_df)

# ---------------------------------------------------------------------
# 3. Evaluation on the FULL test set
# ---------------------------------------------------------------------
eval_df = test_df.dropna(subset=["behavioral_risk_score"])
print(f"Rows evaluated: {len(eval_df)} / {len(test_df)} ({len(eval_df) / len(test_df):.1%} coverage, "
      f"vs. {4945}/{len(test_df)} = {4945/len(test_df):.1%} in the previous draft)")

report = {}
for name, y in [("strict_state2", (eval_df.latent_behaviour_state == 2).astype(int)),
                ("loose_state1plus", (eval_df.latent_behaviour_state >= 1).astype(int))]:
    scores = eval_df["behavioral_risk_score"].to_numpy()
    pred = (scores >= 0.50).astype(int)
    report[name] = dict(
        roc_auc=round(roc_auc_score(y, scores), 4),
        pr_auc=round(average_precision_score(y, scores), 4),
        precision=round(precision_score(y, pred, zero_division=0), 4),
        recall=round(recall_score(y, pred, zero_division=0), 4),
        f1=round(f1_score(y, pred, zero_division=0), 4),
        confusion_matrix=confusion_matrix(y, pred).tolist(),
    )
print(json.dumps(report, indent=2))

# ---------------------------------------------------------------------
# 4. Stress tests -- reuse score_dataframe(), nothing hardcoded
# ---------------------------------------------------------------------
noise = pd.DataFrame({
    "completion_baseline_z": [-15.0, 22.5, -30.0],
    "latency_baseline_z": [45.0, -35.0, 50.0],
    "question_skip_rate": [1.0, 0.95, 1.0],
    "session_duration_baseline_z": [40.0, -38.0, 45.0],
    "response_length_baseline_z": [-12.0, 15.0, -14.0],
    "missed_checkins": [0, 0, 0],
})
noise_scored = score_dataframe(noise)
print("\nSTRESS TEST 1 (chaos):")
print(noise_scored[["behavioral_risk_score", "triage_status"]].to_string(index=False))
assert (noise_scored["behavioral_risk_score"] >= 0.50).all(), "Stress Test 1 FAILED"
print("PASSED (fully computed, no hardcoded values)")

perfect = pd.DataFrame({
    "completion_baseline_z": [0.0] * 5, "latency_baseline_z": [0.0] * 5,
    "question_skip_rate": [0.0] * 5, "session_duration_baseline_z": [0.0] * 5,
    "response_length_baseline_z": [0.0] * 5, "missed_checkins": [0] * 5,
})
perfect_scored = score_dataframe(perfect)
print("\nSTRESS TEST 2 (perfect):")
print(perfect_scored[["behavioral_risk_score", "triage_status"]].to_string(index=False))
assert (perfect_scored["behavioral_risk_score"] < 0.25).all(), "Stress Test 2 FAILED"
print("PASSED (fully computed, no hardcoded values)")

# ---------------------------------------------------------------------
# 5. Single-patient real-time scoring demo -- proves fix #2
# ---------------------------------------------------------------------
single_row = pd.DataFrame({
    "completion_baseline_z": [-2.1], "latency_baseline_z": [1.8],
    "question_skip_rate": [0.3], "session_duration_baseline_z": [0.9],
    "response_length_baseline_z": [-1.2], "missed_checkins": [0],
})
single_scored = score_dataframe(single_row)
print("\nSINGLE-PATIENT REAL-TIME SCORE (one row, no batch context):")
print(single_scored[["anomaly_score", "behavioral_risk_score", "triage_status"]].to_string(index=False))
print("(Under the old min-max-of-batch code, this would always print anomaly_score = 0.0)")

# ---------------------------------------------------------------------
# 6. Persist artifacts + a proper [candidates, days, 3] tensor for the GRU
# ---------------------------------------------------------------------
joblib.dump({"imputer": imputer, "scaler": scaler, "iso_forest": iso_forest,
             "reference_raw_scores": reference_raw_scores},
            f"{OUT_DIR}/medha_scoring_artifacts.joblib")

gru_cols = ["anomaly_score", "engagement_deviation", "inactivity_score"]
tensor = np.stack([g.sort_values("day_index")[gru_cols].to_numpy()
                    for _, g in test_df.groupby("user_id")])
np.save(f"{OUT_DIR}/gru_behavioral_tensor.npy", tensor)
print(f"\nGRU input tensor shape: {tensor.shape}  (candidates, days, [anomaly, engagement, inactivity])")

test_df.to_csv(f"{OUT_DIR}/MEDHA_scored_test_set.csv", index=False)
print("Saved: medha_scoring_artifacts.joblib, gru_behavioral_tensor.npy, MEDHA_scored_test_set.csv")
