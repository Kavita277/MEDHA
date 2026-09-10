# MEDHA V2 — Step 12: GRU Temporal Sequence Audit Report

## Overview

This report documents the construction of the V2 GRU temporal sequence dataset, replacing the V1 GRU's feature pipeline which contained severe DDS leakage.

**Purpose**: Build the temporal sliding-window dataset for the GRU future-risk classifier using the authoritative V2 victim-level split and explicit V2 feature whitelist.

**Target**: `Future_Escalation_Label` (binary: will escalation occur in the next 7 days?)

**Status**: COMPLETE — Dataset generated. Model training deferred to Step 13.

---

## V1 GRU Leakage Findings

| Issue | Severity | Detail |
|---|---|---|
| **No explicit feature whitelist** | CRITICAL | V1 `preprocessing.py::get_feature_columns()` selected ALL numeric columns, including DDS-derived features |
| **DDS-derived features as inputs** | CRITICAL | `Previous_DDS`, `Rolling_DDS_Mean`, `DDS_Slope`, `Baseline_DDS`, `DDS` itself were all used as model inputs |
| **Hardcoded 72 features** | HIGH | V1 inference API expected 72 features (all numeric columns in dataset) |
| **No victim-level split** | HIGH | V1 did not reference the authoritative 700/150/150 split |
| **No categorical encoding** | LOW | Non-numeric columns silently dropped |

> **Resolution**: V1 engine preserved intact. V2 dataset built from scratch with explicit leakage-free whitelist.

---

## V2 Feature Whitelist (57 Features)

The whitelist contains all 60 V2-approved features minus 3 non-numeric (`Case_Type`, `Case_Stage`, `Episode_Severity`).

Every feature is validated against `v2_feature_policy.validate_dds_features()`.

### Feature Groups

| Group | Count | Features |
|---|---|---|
| **Structured / Context** | 8 | `Checkin_Available`, `Mood`, `Stress`, `Sleep`, `Functioning`, `Safety`, `Social_Support_Checkin`, `Self_Reported_Wellbeing` |
| **Protection / Events / Clinical** | 15 | `Threat_Event`, `Upcoming_Hearing`, `Hearing_Completed`, `Investigation_Delay`, `Compensation_Delay`, `Relocation_Stress`, `Rehabilitation_Issue`, `Protection_Event`, `Family_Support`, `Social_Support`, `Therapist_Engagement`, `Access_To_Services`, `Stable_Housing`, `Other_Protective_Factors`, `Recent_Episode`, `Family_Reported_Episode` |
| **Behaviour / Engagement** | 7 | `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation` |
| **Text** | 6 | `Text_Available`, `Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency` |
| **Voice** | 6 | `Voice_Available`, `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator` |
| **Baselines / Trends** | 11 | `Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Text_Distress`, `Baseline_Voice_Distress`, `Baseline_Checkin_Distress`, `Text_Distress_Deviation`, `Voice_Distress_Deviation`, `Behaviour_Trend`, `Engagement_Trend`, `Text_Distress_Trend`, `Voice_Distress_Trend` |
| **Availability / Observation** | 3 | `Diary_Available`, `Therapist_Observation_Available`, `Therapist_Observation_Score` |
| **TOTAL** | **57** | |

### Explicitly Excluded (17 features verified absent)

`Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Recent_Change_Rate`, `Recent_Max_DDS`, `Recent_Min_DDS`, `Delta_DDS`, `DDS_Deviation_From_Baseline`, `Baseline_DDS`, `DDS`, `Future_Escalation_Label`, `Trajectory_State`, `Discordance_Test_Feature`, `Discordance_Example_Flag`, `Intervention`, `Follow_Up`

---

## Sequence Construction Methodology

### Sliding Window Configuration

| Parameter | Value |
|---|---|
| Window size | 7 timepoints |
| Target column | `Future_Escalation_Label` |
| Window alignment | `features[t-7:t]` predicts `target[t]` |
| NaN target handling | Skip window if target is NaN |
| Feature NaN handling | Replace NaN and ±inf with 0.0 before windowing |
| Grouping | Per `Victim_ID`, sorted by `Timepoint` |

### Window Construction Logic

For each victim (30 timepoints, sorted by Timepoint):
1. For `end_idx` from 7 to 29 (inclusive):
   - If `Future_Escalation_Label[end_idx]` is NaN → skip
   - Window = features at timepoints `[end_idx-7, end_idx)` (7 timesteps)
   - Label = `Future_Escalation_Label[end_idx]`
2. Timepoints 24–30 have 100% NaN targets → always skipped
3. Valid target timepoints: 7–23 = **16 windows per victim** (some have additional NaN at other timepoints)

---

## Dataset Statistics

### Window Counts

| Split | Victims | Windows | Shape | Positive | Negative | Pos Rate |
|---|---|---|---|---|---|---|
| **Train** | 700 | 11,200 | (11200, 7, 57) | 961 | 10,239 | 8.58% |
| **Validation** | 150 | 2,400 | (2400, 7, 57) | 238 | 2,162 | 9.92% |
| **Test** | 150 | 2,400 | (2400, 7, 57) | 249 | 2,151 | 10.38% |
| **Total** | 1,000 | 16,000 | — | 1,448 | 14,552 | 9.05% |

### Scaler

- Type: `StandardScaler`
- Fitted on: Train windows only (78,400 rows = 11,200 windows × 7 timesteps)
- Applied to: All three splits
- `n_samples_seen_`: 78,400

---

## Leakage Audit Results

### Test Suite: 69/69 PASSED

| Test Category | Tests | Status |
|---|---|---|
| **Victim Isolation** | Train/Val, Train/Test, Val/Test overlap; victim counts | 4/4 PASSED |
| **Feature Policy** | Excluded, target, quarantined, post-hoc, ID/metadata, forbidden, central validation | 7/7 PASSED |
| **Feature Count** | 57 features, no duplicates, X dimension | 3/3 PASSED |
| **Window Shapes** | 3D arrays, y matches X, vids matches X | 5/5 PASSED |
| **No NaN** | X and y for all splits, no inf | 9/9 PASSED |
| **Scaler Integrity** | n_samples, n_features, config match | 3/3 PASSED |
| **Label Distribution** | Binary labels, positive rate, config match | 5/5 PASSED |
| **Sequence Counts** | Shapes match config, plausible total, train ratio | 3/3 PASSED |
| **Data Types** | float32 for X and y | 2/2 PASSED |
| **Artifact Completeness** | 14 files exist and non-empty | 28/28 PASSED |

---

## Saved Artifacts

Location: `engine/models/v2/gru_sequences/`

| File | Description |
|---|---|
| `X_train.npy` | Scaled train feature windows (11200, 7, 57) |
| `y_train.npy` | Train labels (11200,) |
| `victim_ids_train.npy` | Train victim IDs (11200,) |
| `X_val.npy` | Scaled validation feature windows (2400, 7, 57) |
| `y_val.npy` | Validation labels (2400,) |
| `victim_ids_val.npy` | Validation victim IDs (2400,) |
| `X_test.npy` | Scaled test feature windows (2400, 7, 57) |
| `y_test.npy` | Test labels (2400,) |
| `victim_ids_test.npy` | Test victim IDs (2400,) |
| `X_train_unscaled.npy` | Unscaled train windows (reproducibility) |
| `X_val_unscaled.npy` | Unscaled validation windows (reproducibility) |
| `X_test_unscaled.npy` | Unscaled test windows (reproducibility) |
| `scaler.joblib` | Train-fitted StandardScaler |
| `feature_config.json` | Feature list, shapes, label stats, metadata |

---

## Key Scripts

| File | Purpose |
|---|---|
| `engine/v2/build_v2_gru_sequences.py` | Sequence construction pipeline |
| `engine/tests/test_v2_gru_sequences.py` | 69-test leakage audit suite |
| `engine/v2/v2_feature_policy.py` | Central feature policy (unchanged) |
