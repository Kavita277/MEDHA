"""
MEDHA V2 — Step 12: Build GRU Temporal Sequences

This script:
1. Loads v2_longitudinal_split.csv (authoritative V2 split)
2. Validates an immutable 57-feature whitelist against v2_feature_policy
3. Builds sliding-window sequences (window_size=7) per victim
4. Fits StandardScaler on Train windows ONLY
5. Saves X/y/victim_ids for Train/Val/Test, scaler, and feature_config.json

Target: Future_Escalation_Label (binary)
DO NOT train the GRU model in this script.
"""

import numpy as np
import pandas as pd
import json
import os
import sys
import joblib
from sklearn.preprocessing import StandardScaler

# ==============================================================
# PATHS
# ==============================================================
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.dirname(__file__)

DATA_PATH = os.path.join(ENGINE_DIR, 'data', 'processed', 'v2_longitudinal_split.csv')
OUTPUT_DIR = os.path.join(ENGINE_DIR, 'models', 'v2', 'gru_sequences')

# ==============================================================
# IMMUTABLE FEATURE WHITELIST — 57 NUMERIC APPROVED FEATURES
# ==============================================================
# These are ALL 60 V2-approved features MINUS the 3 non-numeric:
#   Case_Type (str), Case_Stage (str), Episode_Severity (str)
# Every feature here MUST pass v2_feature_policy.validate_dds_features().
#
# This list is an IMMUTABLE LITERAL — not derived from DataFrame introspection.

V2_GRU_FEATURE_WHITELIST = [
    # Structured / Case / Context (8 numeric out of 10)
    "Checkin_Available",
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",

    # Context / Protection Events / Clinical Episodes (15 numeric out of 17)
    "Threat_Event",
    "Upcoming_Hearing",
    "Hearing_Completed",
    "Investigation_Delay",
    "Compensation_Delay",
    "Relocation_Stress",
    "Rehabilitation_Issue",
    "Protection_Event",
    "Family_Support",
    "Social_Support",
    "Therapist_Engagement",
    "Access_To_Services",
    "Stable_Housing",
    "Other_Protective_Factors",
    "Recent_Episode",
    # Episode_Severity excluded (non-numeric str)
    "Family_Reported_Episode",

    # Behaviour / Engagement (7)
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",

    # Text (6 direct)
    "Text_Available",
    "Text_Distress",
    "Fear",
    "Threat_Context",
    "Negative_Affect",
    "Urgency",

    # Voice (6 direct)
    "Voice_Available",
    "Voice_Distress",
    "Pause_Ratio",
    "Speech_Rate_Deviation",
    "Energy_Deviation",
    "Acoustic_Indicator",

    # Baselines and Trends (11)
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Baseline_Text_Distress",
    "Baseline_Voice_Distress",
    "Baseline_Checkin_Distress",
    "Text_Distress_Deviation",
    "Voice_Distress_Deviation",
    "Behaviour_Trend",
    "Engagement_Trend",
    "Text_Distress_Trend",
    "Voice_Distress_Trend",

    # Other Availability / Observation (3)
    "Diary_Available",
    "Therapist_Observation_Available",
    "Therapist_Observation_Score",
]

assert len(V2_GRU_FEATURE_WHITELIST) == 57, (
    f"Expected 57 features, got {len(V2_GRU_FEATURE_WHITELIST)}"
)

# Verify no duplicates
assert len(set(V2_GRU_FEATURE_WHITELIST)) == 57, "Duplicate features in whitelist!"

# ==============================================================
# CONFIGURATION
# ==============================================================
WINDOW_SIZE = 7
TARGET_COLUMN = "Future_Escalation_Label"
SEED = 42

# ==============================================================
# VALIDATE FEATURE WHITELIST AGAINST CENTRAL POLICY
# ==============================================================
print("=" * 60)
print("MEDHA V2 Step 12 — GRU Temporal Sequence Builder")
print("=" * 60)

sys.path.insert(0, V2_DIR)
from v2_feature_policy import (
    validate_dds_features,
    V2_DDS_EXCLUDED_FEATURES,
    V2_DDS_TARGET_FEATURES,
    V2_DDS_QUARANTINED_FEATURES,
    V2_DDS_POST_HOC_FEATURES,
)

print("\n[1/7] Validating feature whitelist against v2_feature_policy...")
validate_dds_features(V2_GRU_FEATURE_WHITELIST)
print(f"  PASS: All {len(V2_GRU_FEATURE_WHITELIST)} features are V2-approved")

# Double-check: no excluded features
for f in V2_GRU_FEATURE_WHITELIST:
    assert f not in V2_DDS_EXCLUDED_FEATURES, f"LEAKAGE: '{f}' is an excluded DDS feature!"
    assert f not in V2_DDS_TARGET_FEATURES, f"LEAKAGE: '{f}' is a target feature!"
    assert f not in V2_DDS_QUARANTINED_FEATURES, f"QUARANTINE: '{f}' is quarantined!"
    assert f not in V2_DDS_POST_HOC_FEATURES, f"LEAKAGE: '{f}' is a post-hoc feature!"
print("  PASS: No excluded, target, quarantined, or post-hoc features in whitelist")

# Verify forbidden features are NOT present
EXPLICITLY_FORBIDDEN = [
    "Previous_DDS", "Rolling_DDS_Mean", "Rolling_DDS_SD", "DDS_Slope",
    "Recent_Change_Rate", "Recent_Max_DDS", "Recent_Min_DDS", "Delta_DDS",
    "DDS_Deviation_From_Baseline", "Baseline_DDS",
    "DDS", "Future_Escalation_Label",
    "Trajectory_State", "Discordance_Test_Feature", "Discordance_Example_Flag",
    "Intervention", "Follow_Up",
]
for f in EXPLICITLY_FORBIDDEN:
    assert f not in V2_GRU_FEATURE_WHITELIST, f"FORBIDDEN: '{f}' found in whitelist!"
print(f"  PASS: {len(EXPLICITLY_FORBIDDEN)} explicitly forbidden features verified absent")

# ==============================================================
# LOAD DATA
# ==============================================================
print(f"\n[2/7] Loading dataset: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"  Shape: {df.shape}")
print(f"  Victims: {df['Victim_ID'].nunique()}")

# Verify authoritative split
split_counts = df.groupby('Split')['Victim_ID'].nunique()
assert split_counts['train'] == 700, f"Expected 700 train victims, got {split_counts['train']}"
assert split_counts['validation'] == 150, f"Expected 150 val victims, got {split_counts['validation']}"
assert split_counts['test'] == 150, f"Expected 150 test victims, got {split_counts['test']}"
print("  PASS: 700/150/150 victim split verified")

# Verify no victim overlap
train_vids = set(df[df['Split'] == 'train']['Victim_ID'].unique())
val_vids = set(df[df['Split'] == 'validation']['Victim_ID'].unique())
test_vids = set(df[df['Split'] == 'test']['Victim_ID'].unique())
assert len(train_vids & val_vids) == 0, "LEAKAGE: Train/Val victim overlap!"
assert len(train_vids & test_vids) == 0, "LEAKAGE: Train/Test victim overlap!"
assert len(val_vids & test_vids) == 0, "LEAKAGE: Val/Test victim overlap!"
print("  PASS: Zero victim overlap across all splits")

# Verify all whitelist features exist in data
missing = [f for f in V2_GRU_FEATURE_WHITELIST if f not in df.columns]
assert len(missing) == 0, f"Features missing from dataset: {missing}"
print(f"  PASS: All {len(V2_GRU_FEATURE_WHITELIST)} features present in dataset")

# Verify all whitelist features are numeric
non_numeric = [f for f in V2_GRU_FEATURE_WHITELIST if not pd.api.types.is_numeric_dtype(df[f])]
assert len(non_numeric) == 0, f"Non-numeric features in whitelist: {non_numeric}"
print(f"  PASS: All {len(V2_GRU_FEATURE_WHITELIST)} features are numeric")

# ==============================================================
# PREPARE FEATURES — NaN/Inf handling
# ==============================================================
print("\n[3/7] Preparing features (NaN -> 0.0, inf -> 0.0)...")
for f in V2_GRU_FEATURE_WHITELIST:
    df[f] = df[f].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(np.float32)

nan_check = df[V2_GRU_FEATURE_WHITELIST].isna().sum().sum()
assert nan_check == 0, f"Still have {nan_check} NaN values after preprocessing!"
print(f"  PASS: Zero NaN/inf in feature matrix")

# ==============================================================
# BUILD SLIDING WINDOWS
# ==============================================================
print(f"\n[4/7] Building sliding windows (window_size={WINDOW_SIZE})...")

def build_sliding_windows_for_split(split_df, split_name):
    """Build (X, y, victim_ids) for a single split using sliding windows."""
    sequences = []
    labels = []
    victim_ids_out = []

    for victim_id, victim_data in split_df.groupby("Victim_ID", sort=True):
        victim_data = victim_data.sort_values("Timepoint")
        features = victim_data[V2_GRU_FEATURE_WHITELIST].to_numpy(dtype=np.float32)
        targets = victim_data[TARGET_COLUMN].to_numpy()

        for end_idx in range(WINDOW_SIZE, len(victim_data)):
            target_val = targets[end_idx]
            if np.isnan(target_val):
                continue
            # Window: [end_idx - WINDOW_SIZE, end_idx) — does NOT include the target timestep
            window = features[end_idx - WINDOW_SIZE:end_idx]
            sequences.append(window)
            labels.append(target_val)
            victim_ids_out.append(victim_id)

    if not sequences:
        raise ValueError(f"No valid sequences found for split '{split_name}'!")

    X = np.stack(sequences)
    y = np.asarray(labels, dtype=np.float32)
    vids = np.asarray(victim_ids_out)

    print(f"  {split_name:>10s}: {X.shape[0]:>6d} windows, "
          f"shape={X.shape}, pos={int((y==1).sum())}, neg={int((y==0).sum())})")
    return X, y, vids


# Split data
train_df = df[df['Split'] == 'train'].copy()
val_df = df[df['Split'] == 'validation'].copy()
test_df = df[df['Split'] == 'test'].copy()

X_train, y_train, vids_train = build_sliding_windows_for_split(train_df, "Train")
X_val, y_val, vids_val = build_sliding_windows_for_split(val_df, "Validation")
X_test, y_test, vids_test = build_sliding_windows_for_split(test_df, "Test")

# Verify shapes
assert X_train.ndim == 3 and X_train.shape[1] == WINDOW_SIZE and X_train.shape[2] == 57
assert X_val.ndim == 3 and X_val.shape[1] == WINDOW_SIZE and X_val.shape[2] == 57
assert X_test.ndim == 3 and X_test.shape[1] == WINDOW_SIZE and X_test.shape[2] == 57
assert y_train.ndim == 1 and len(y_train) == X_train.shape[0]
assert y_val.ndim == 1 and len(y_val) == X_val.shape[0]
assert y_test.ndim == 1 and len(y_test) == X_test.shape[0]
print("  PASS: All shapes verified")

# Verify no NaN in targets
assert not np.any(np.isnan(y_train)), "NaN in y_train!"
assert not np.any(np.isnan(y_val)), "NaN in y_val!"
assert not np.any(np.isnan(y_test)), "NaN in y_test!"
print("  PASS: Zero NaN in all targets")

# Verify no NaN in features
assert not np.any(np.isnan(X_train)), "NaN in X_train!"
assert not np.any(np.isnan(X_val)), "NaN in X_val!"
assert not np.any(np.isnan(X_test)), "NaN in X_test!"
print("  PASS: Zero NaN in all feature windows")

# Verify victim isolation
train_vids_in_seq = set(vids_train)
val_vids_in_seq = set(vids_val)
test_vids_in_seq = set(vids_test)
assert len(train_vids_in_seq & val_vids_in_seq) == 0, "LEAKAGE: Train/Val victim overlap in sequences!"
assert len(train_vids_in_seq & test_vids_in_seq) == 0, "LEAKAGE: Train/Test victim overlap in sequences!"
assert len(val_vids_in_seq & test_vids_in_seq) == 0, "LEAKAGE: Val/Test victim overlap in sequences!"
print("  PASS: Zero victim overlap in constructed sequences")

# ==============================================================
# FIT SCALER ON TRAIN ONLY
# ==============================================================
print(f"\n[5/7] Fitting StandardScaler on Train windows only...")
scaler = StandardScaler()

# Reshape 3D -> 2D for fitting: (n_windows * window_size, n_features)
n_train, ws, nf = X_train.shape
X_train_2d = X_train.reshape(n_train * ws, nf)
scaler.fit(X_train_2d)

print(f"  Scaler fitted on {n_train * ws} rows ({n_train} windows × {ws} timesteps)")
print(f"  n_samples_seen_: {scaler.n_samples_seen_}")

# Transform all splits
X_train_scaled = scaler.transform(X_train_2d).reshape(n_train, ws, nf)
X_val_scaled = scaler.transform(X_val.reshape(-1, nf)).reshape(X_val.shape)
X_test_scaled = scaler.transform(X_test.reshape(-1, nf)).reshape(X_test.shape)

# Verify no NaN after scaling
assert not np.any(np.isnan(X_train_scaled)), "NaN in X_train_scaled!"
assert not np.any(np.isnan(X_val_scaled)), "NaN in X_val_scaled!"
assert not np.any(np.isnan(X_test_scaled)), "NaN in X_test_scaled!"
print("  PASS: Zero NaN after scaling")

# Convert to float32 for storage efficiency
X_train_scaled = X_train_scaled.astype(np.float32)
X_val_scaled = X_val_scaled.astype(np.float32)
X_test_scaled = X_test_scaled.astype(np.float32)

# ==============================================================
# SAVE ARTIFACTS
# ==============================================================
print(f"\n[6/7] Saving artifacts to {OUTPUT_DIR}")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Arrays
np.save(os.path.join(OUTPUT_DIR, 'X_train.npy'), X_train_scaled)
np.save(os.path.join(OUTPUT_DIR, 'y_train.npy'), y_train)
np.save(os.path.join(OUTPUT_DIR, 'victim_ids_train.npy'), vids_train)

np.save(os.path.join(OUTPUT_DIR, 'X_val.npy'), X_val_scaled)
np.save(os.path.join(OUTPUT_DIR, 'y_val.npy'), y_val)
np.save(os.path.join(OUTPUT_DIR, 'victim_ids_val.npy'), vids_val)

np.save(os.path.join(OUTPUT_DIR, 'X_test.npy'), X_test_scaled)
np.save(os.path.join(OUTPUT_DIR, 'y_test.npy'), y_test)
np.save(os.path.join(OUTPUT_DIR, 'victim_ids_test.npy'), vids_test)

# Also save unscaled arrays for reproducibility audits
np.save(os.path.join(OUTPUT_DIR, 'X_train_unscaled.npy'), X_train)
np.save(os.path.join(OUTPUT_DIR, 'X_val_unscaled.npy'), X_val)
np.save(os.path.join(OUTPUT_DIR, 'X_test_unscaled.npy'), X_test)

# Scaler
joblib.dump(scaler, os.path.join(OUTPUT_DIR, 'scaler.joblib'))

# Feature config
feature_config = {
    "step": "Step 12 — GRU Temporal Sequence Construction",
    "source_data": "engine/data/processed/v2_longitudinal_split.csv",
    "target_column": TARGET_COLUMN,
    "window_size": WINDOW_SIZE,
    "n_features": len(V2_GRU_FEATURE_WHITELIST),
    "feature_whitelist": V2_GRU_FEATURE_WHITELIST,
    "excluded_non_numeric_approved": ["Case_Type", "Case_Stage", "Episode_Severity"],
    "nan_handling": "NaN and ±inf replaced with 0.0 before sequence construction",
    "scaler": "StandardScaler fitted on Train windows only",
    "shapes": {
        "X_train": list(X_train_scaled.shape),
        "y_train": list(y_train.shape),
        "X_val": list(X_val_scaled.shape),
        "y_val": list(y_val.shape),
        "X_test": list(X_test_scaled.shape),
        "y_test": list(y_test.shape),
    },
    "label_distribution": {
        "train": {"pos": int((y_train == 1).sum()), "neg": int((y_train == 0).sum()), "total": int(len(y_train))},
        "val": {"pos": int((y_val == 1).sum()), "neg": int((y_val == 0).sum()), "total": int(len(y_val))},
        "test": {"pos": int((y_test == 1).sum()), "neg": int((y_test == 0).sum()), "total": int(len(y_test))},
    },
    "victim_counts": {
        "train": len(train_vids_in_seq),
        "val": len(val_vids_in_seq),
        "test": len(test_vids_in_seq),
    },
    "scaler_n_samples_seen": int(scaler.n_samples_seen_),
    "seed": SEED,
}

with open(os.path.join(OUTPUT_DIR, 'feature_config.json'), 'w') as f:
    json.dump(feature_config, f, indent=2)

print(f"  Saved 15 files to {OUTPUT_DIR}")

# ==============================================================
# FINAL SUMMARY
# ==============================================================
print(f"\n[7/7] Final Summary")
print("=" * 60)
print(f"  Features:    {len(V2_GRU_FEATURE_WHITELIST)} (explicit whitelist, V2-validated)")
print(f"  Window size: {WINDOW_SIZE}")
print(f"  Target:      {TARGET_COLUMN}")
print(f"  Train:       {X_train_scaled.shape[0]:>6d} windows  (pos={int((y_train==1).sum())}, neg={int((y_train==0).sum())})")
print(f"  Validation:  {X_val_scaled.shape[0]:>6d} windows  (pos={int((y_val==1).sum())}, neg={int((y_val==0).sum())})")
print(f"  Test:        {X_test_scaled.shape[0]:>6d} windows  (pos={int((y_test==1).sum())}, neg={int((y_test==0).sum())})")
print(f"  Scaler:      StandardScaler fitted on {scaler.n_samples_seen_} Train rows")
print(f"  Output dir:  {OUTPUT_DIR}")
print("=" * 60)
print("STEP 12 COMPLETE — Dataset generated. DO NOT train the model.")
