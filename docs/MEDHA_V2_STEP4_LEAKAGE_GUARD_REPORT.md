# MEDHA V2 STEP 4 — CENTRALIZED DDS LEAKAGE GUARD REPORT

## 1. Purpose

To establish a **Single Source of Truth** for feature eligibility in V2 DDS modeling, preventing data leakage. The step replaces the dangerous "select all numeric columns except..." logic with an explicit, hard-failing whitelist that explicitly bans target-derived historical columns from being used to predict current-timepoint DDS.

## 2. Repository Audit Findings

An audit of the repository revealed the dangerous pattern in several V1 files (e.g., `engine/fusion_engine/final_fusion_experiments.py`, `evaluate_medha_pipeline.py`, `fusion_validation_pipeline.py`, `generate_oof_predictions.py`, `evaluate_fusion.py`):

```python
numeric_cols = [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
gru_features = numeric_cols[:72]
```

This logic automatically includes any new numeric column and relies entirely on a manual exclusion list and arbitrary column slicing (`[:72]`). This is extremely fragile. It guarantees that if a new leaky feature is added to the dataset, it will silently become a model input. The V2 guard completely solves this by requiring explicit inclusion.

## 3. DDS Target Definition

DDS is the current-timepoint prediction target for specialist models.
`Future_Escalation_Label` is the future prediction target for the temporal model (GRU).
Neither can be used as input features to predict themselves.

## 4. Approved Feature Whitelist (60 Unique Features)

Only features that represent information genuinely available at the current timepoint and are not mechanically derived from the DDS target are approved.

**Structured / Case / Context:**
- `Case_Type`
- `Case_Stage`
- `Checkin_Available`
- `Mood`
- `Stress`
- `Sleep`
- `Functioning`
- `Safety`
- `Social_Support_Checkin`
- `Self_Reported_Wellbeing`
- `Threat_Event`
- `Upcoming_Hearing`
- `Hearing_Completed`
- `Investigation_Delay`
- `Compensation_Delay`
- `Relocation_Stress`
- `Rehabilitation_Issue`
- `Protection_Event`
- `Family_Support`
- `Social_Support`
- `Therapist_Engagement`
- `Access_To_Services`
- `Stable_Housing`
- `Other_Protective_Factors`
- `Recent_Episode`
- `Episode_Severity`
- `Family_Reported_Episode`

**Behaviour:**
- `Missed_Checkin`
- `Interaction_Frequency_7d`
- `Session_Duration_Minutes`
- `Engagement_Score`
- `Engagement_Deviation`
- `Response_Delay_Hours`
- `Response_Delay_Deviation`

**Text:**
- `Text_Available`
- `Text_Distress`
- `Fear`
- `Threat_Context`
- `Negative_Affect`
- `Urgency`

**Voice:**
- `Voice_Available`
- `Voice_Distress`
- `Pause_Ratio`
- `Speech_Rate_Deviation`
- `Energy_Deviation`
- `Acoustic_Indicator`

**Baselines & Trends (Approved in Step 2):**
- `Baseline_Response_Delay`
- `Baseline_Engagement`
- `Baseline_Text_Distress`
- `Baseline_Voice_Distress`
- `Baseline_Checkin_Distress`
- `Text_Distress_Deviation`
- `Voice_Distress_Deviation`
- `Behaviour_Trend`
- `Engagement_Trend`
- `Text_Distress_Trend`
- `Voice_Distress_Trend`
- `Diary_Available`
- `Therapist_Observation_Available`
- `Therapist_Observation_Score`

## 5. Excluded Feature List (Leaky)

- `Previous_DDS`
- `Rolling_DDS_Mean`
- `Rolling_DDS_SD`
- `DDS_Slope`
- `Recent_Change_Rate`
- `Recent_Max_DDS`
- `Recent_Min_DDS`
- `Delta_DDS`
- `DDS_Deviation_From_Baseline`
- `Baseline_DDS`

## 6. Target, Metadata, and Post-Hoc Exclusions

- **Targets:** `DDS`, `Future_Escalation_Label`
- **Metadata:** `Victim_ID`, `Case_ID`, `Timepoint`, `Date_Time`
- **Post-Hoc:** `Intervention`, `Follow_Up`

## 7. Quarantined Feature List

- `Trajectory_State`
- `Discordance_Test_Feature`
- `Discordance_Example_Flag`
- `Diary_Distress_Feature`
- `Diary_Length`

## 8. Leakage Rationale & Major Exclusions

The major excluded features (`Previous_DDS`, `Rolling_DDS_Mean`, etc.) mechanically contain previous observations of the target variable (`DDS`). If a current-timepoint model relies on previous labels to predict current labels, it suffers from severe target leakage, artificially inflating its apparent accuracy while reducing its ability to actually learn the relationship between underlying stressors (text, voice, behaviour) and the target.

`Baseline_DDS` is excluded because it is computed from the underlying data generation process's initial state for the target variable.

`Trajectory_State` is quarantined because its construction logic may encode future or historical trajectory definitions.

## 9. Hard-Fail Validation Behaviour

The policy uses two functions:
1. `validate_dds_features(features)`: Hard-fails with a `ValueError` if a script explicitly requests *any* unapproved feature. This stops accidental inclusion of `Previous_DDS` immediately.
2. `get_allowed_dds_features(requested_features)`: Validates a list of requested features. If *any* feature in the list is unapproved, unknown, a target, or metadata, it hard-fails with a `ValueError`. It intentionally does not silently drop unknown features to prevent masking policy mistakes.
3. `get_all_approved_dds_features()`: A helper function that returns the complete whitelist for introspection.

## 10. Test Results

`python engine/test_v2_feature_policy.py` passed all individual assertions:
- Explicit rejection of all 10 leaky features.
- Explicit rejection of targets, metadata, post-hoc outcomes.
- Explicit rejection of all 5 quarantined features.
- Explicit rejection of unknown feature names.
- Explicit rejection of duplicate features in the request list.
- Explicit hard failure when an unapproved feature is passed to `get_allowed_dds_features`.
- Successful generation of JSON policy mapping.

## 11. Exact Files Created/Modified

**Created:**
- `engine/v2_feature_policy.py`
- `engine/test_v2_feature_policy.py`
- `engine/data/processed/v2_feature_policy.json`
- `docs/MEDHA_V2_STEP4_LEAKAGE_GUARD_REPORT.md`

**Modified:**
- None.

## 12. Confirmations

- **No Models Trained:** Confirmed. This step exclusively built configuration logic.
- **V1 Untouched:** Confirmed. All V1 scripts and pipelines are unmodified and preserve their original logic.
- **V2 Dataset Untouched:** Confirmed. Both the split files and the original Excel file were not altered.
