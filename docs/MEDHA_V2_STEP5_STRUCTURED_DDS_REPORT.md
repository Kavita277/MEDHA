# MEDHA V2 STEP 5 — STRUCTURED DDS REGRESSOR REPORT (UPDATED WITH SPECIALIST BOUNDARY PATCH)

## 1. Objective

Train and validate the V2 **Clean Structured DDS Regression Specialist** that predicts current-timepoint `DDS` from genuinely structured, case, context, clinical, and behavioural observations using the regenerated dataset and victim-level held-out evaluation.

---

## 2. Global Feature Universe vs. Specialist Feature Boundaries

A critical architectural distinction is maintained between the global leakage guard policy and individual specialist feature subsets:

### A. Global Approved Feature Universe (60 Features)
- Defined in `engine/v2/v2_feature_policy.py` (`V2_DDS_APPROVED_FEATURES`).
- Represents the complete set of variables in `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx` that are temporally valid at timepoint $T$ and free of target-derived historical leakage (e.g. `Previous_DDS`, `Rolling_DDS_Mean`, `DDS_Slope`, `Baseline_DDS`, `Delta_DDS`).

### B. Clean Structured Specialist Subset (42 Features)
- Defined in `engine/v2/v2_feature_policy.py` (`V2_STRUCTURED_DDS_FEATURES`).
- The Structured Specialist consumes **only** structured, case, context, clinical episode, and behavioural features.
- All Text-derived (9) and Voice-derived (9) features are strictly excluded to preserve specialist boundary isolation.

### C. Excluded Modality Features (18 Features)
| Modality | Features Excluded from Structured Specialist | Rationale |
|---|---|---|
| **Text** (9) | `Text_Available`, `Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`, `Baseline_Text_Distress`, `Text_Distress_Deviation`, `Text_Distress_Trend` | Belongs exclusively to the Text Specialist |
| **Voice** (9) | `Voice_Available`, `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`, `Baseline_Voice_Distress`, `Voice_Distress_Deviation`, `Voice_Distress_Trend` | Belongs exclusively to the Voice Specialist |

---

## 3. Approved Structured Specialist Feature Whitelist (42 Features)

### Structured / Case / Check-in Context (10)
`Case_Type`, `Case_Stage`, `Checkin_Available`, `Mood`, `Stress`, `Sleep`, `Functioning`, `Safety`, `Social_Support_Checkin`, `Self_Reported_Wellbeing`

### Context / Legal / Protection Events / Clinical Episodes (17)
`Threat_Event`, `Upcoming_Hearing`, `Hearing_Completed`, `Investigation_Delay`, `Compensation_Delay`, `Relocation_Stress`, `Rehabilitation_Issue`, `Protection_Event`, `Family_Support`, `Social_Support`, `Therapist_Engagement`, `Access_To_Services`, `Stable_Housing`, `Other_Protective_Factors`, `Recent_Episode`, `Episode_Severity`, `Family_Reported_Episode`

### Behavioural / Engagement (7)
`Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation`

### Structured Baseline / Trend / Clinical Observations (8)
`Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Checkin_Distress`, `Behaviour_Trend`, `Engagement_Trend`, `Diary_Available`, `Therapist_Observation_Available`, `Therapist_Observation_Score`

---

## 4. Authoritative Data Split

| Split | Victims | Percentage | Longitudinal Rows | Isolation Check |
|---|---|---|---|---|
| **Train** | 700 | 70.0% | 21,000 | Disjoint |
| **Validation** | 150 | 15.0% | 4,500 | Disjoint |
| **Test** | 150 | 15.0% | 4,500 | Disjoint |
| **Total** | 1,000 | 100.0% | 30,000 | Zero victim overlap |

---

## 5. Preprocessing Pipeline

- **Numeric features (39)**: Imputed with **median** computed exclusively from the 21,000 training rows.
- **Categorical features (3)**: `Case_Type`, `Case_Stage`, `Episode_Severity` imputed with `"MISSING"` and encoded via `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)` fitted on train rows only.
- **No data leakage**: The preprocessor was fitted strictly on `train_df` and applied out-of-sample to `val_df` and `test_df`.

---

## 6. Model Architecture & Hyperparameters

- **Algorithm**: `xgboost.XGBRegressor`
- **Objective**: `reg:squarederror`
- **Number of Estimators**: 300
- **Learning Rate**: 0.05
- **Max Depth**: 5
- **Subsample**: 0.8
- **Colsample By Tree**: 0.8
- **Random Seed**: 42

---

## 7. Evaluation Results — Clean Structured Specialist (42 Features)

### Row-Level Evaluation (Primary Held-Out Metrics)

| Split | Rows | Target Mean (SD) | Pred Mean (SD) | MAE | RMSE | R² | Pearson $r$ | Baseline MAE | Baseline R² | MAE Reduction |
|---|---|---|---|---|---|---|---|---|---|---|
| **Train** | 21,000 | 39.70 (13.07) | 39.70 (10.73) | 5.3719 | 6.7490 | **0.7333** | **0.8571** | 10.6962 | 0.0000 | **-49.8%** |
| **Validation** | 4,500 | 40.73 (12.77) | 40.56 (10.27) | 6.0616 | 7.5970 | **0.6462** | **0.8040** | 10.4499 | -0.0065 | **-42.0%** |
| **Test** | 4,500 | 40.53 (13.14) | 40.70 (10.49) | 6.1611 | 7.7353 | **0.6536** | **0.8086** | 10.8196 | -0.0039 | **-43.1%** |

### Victim-Level Mean Diagnostics

| Split | Victims | Victim MAE | Victim RMSE | Victim R² | Victim Pearson $r$ |
|---|---|---|---|---|---|
| **Train** | 700 | 1.1233 | 1.3885 | 0.9773 | 0.9919 |
| **Validation** | 150 | 1.6594 | 2.0131 | 0.9438 | 0.9776 |
| **Test** | 150 | 1.7280 | 2.1944 | 0.9449 | 0.9781 |

---

## 8. Diagnostic Comparison: Clean Specialist vs. Provisional All-60 Experiment

The provisional all-60-feature experiment is retained as a diagnostic reference:

| Model | Features | Test MAE | Test RMSE | Test R² | Modality Purity |
|---|---|---|---|---|---|
| **Clean Structured Specialist (Final Step 5)** | **42** | **6.1611** | **7.7353** | **0.6536** | **100% Clean (0 Text, 0 Voice)** |
| Provisional All-Approved Diagnostic Experiment | 60 | 5.8859 | 7.3839 | 0.6844 | Multimodal (includes Text & Voice) |
| Naïve Baseline (Predict Train Mean) | 0 | 10.8196 | 13.1688 | -0.0039 | None |

> [!NOTE]
> The clean Structured Specialist captures substantial signal ($R^2 = 0.6536$, 43.1% error reduction over baseline) using purely structured, case, and behavioural data without cross-contaminating text or voice observations.

---

## 9. Feature Importance (Top 20 by Gain — Clean Specialist)

| Rank | Feature | Gain Importance | Category |
|---|---|---|---|
| 1 | `Engagement_Score` | 0.3157 | Behavioural |
| 2 | `Stress` | 0.1087 | Check-in Structured |
| 3 | `Mood` | 0.0796 | Check-in Structured |
| 4 | `Safety` | 0.0655 | Check-in Structured |
| 5 | `Sleep` | 0.0503 | Check-in Structured |
| 6 | `Functioning` | 0.0430 | Check-in Structured |
| 7 | `Engagement_Deviation` | 0.0351 | Behavioural |
| 8 | `Baseline_Checkin_Distress` | 0.0326 | Baseline Trait |
| 9 | `Self_Reported_Wellbeing` | 0.0283 | Check-in Structured |
| 10 | `Compensation_Delay` | 0.0189 | Legal / Case Context |
| 11 | `Baseline_Engagement` | 0.0150 | Baseline Trait |
| 12 | `Relocation_Stress` | 0.0144 | Life Context |
| 13 | `Investigation_Delay` | 0.0141 | Legal / Case Context |
| 14 | `Threat_Event` | 0.0127 | Protection Event |
| 15 | `Upcoming_Hearing` | 0.0107 | Legal / Case Context |
| 16 | `Other_Protective_Factors` | 0.0095 | Protection Context |
| 17 | `Response_Delay_Deviation` | 0.0093 | Behavioural |
| 18 | `Rehabilitation_Issue` | 0.0092 | Protection Context |
| 19 | `Engagement_Trend` | 0.0078 | Trend Observation |
| 20 | `Checkin_Available` | 0.0078 | Availability Flag |

**Modality Purity Verification**: Zero Text and zero Voice features appear in the importance ranking.

---

## 10. Boundary & Leakage Verification Checks

1. **Global Leakage Whitelist**: Passes all assertions; zero overlap with target/lag features.
2. **Text Feature Rejection**: Any inclusion of `Text_Distress`, `Fear`, `Urgency`, `Negative_Affect`, etc. raises `ValueError`.
3. **Voice Feature Rejection**: Any inclusion of `Voice_Distress`, `Pause_Ratio`, `Energy_Deviation`, etc. raises `ValueError`.
4. **Target Isolation**: `DDS` and `Future_Escalation_Label` rejected.
5. **Victim Partitioning**: Strict 700/150/150 victim-level split with 0 victim overlap across all splits.
6. **Train-Only Preprocessing**: Imputers and encoders fitted strictly on 21,000 train rows.

---

## 11. Test Suite Verification

- **Pytest Suite (`pytest engine/tests`)**: **17/17 PASS**
  - `engine/tests/test_v2_feature_policy.py`: 11 tests passed
  - `engine/tests/test_v2_structured_dds.py`: 6 test suites passed
- **Standalone CLI Runners**:
  - `python engine/tests/test_v2_feature_policy.py`: **ALL PASS**
  - `python engine/tests/test_v2_structured_dds.py`: **ALL PASS**

---

## 12. Artifacts Produced

| Artifact File | Description |
|---|---|
| `engine/v2/v2_feature_policy.py` | Central feature policy with explicit modality boundaries |
| `engine/v2/train_v2_structured_dds.py` | Training script for clean 42-feature Structured specialist |
| `engine/tests/test_v2_feature_policy.py` | Policy and boundary tests |
| `engine/tests/test_v2_structured_dds.py` | Structured specialist test suite |
| `engine/models/v2/v2_structured_dds_xgb.json` | Final Clean Structured DDS Regressor |
| `engine/models/v2/v2_structured_dds_preprocessor.pkl` | Train-fitted ColumnTransformer preprocessor |
| `engine/models/v2/v2_structured_dds_features.json` | 42-feature specialist metadata |
| `engine/models/v2/v2_structured_dds_metrics.json` | Evaluation metrics and hyperparameters |
| `engine/models/v2/v2_structured_dds_importance.csv` | Feature importances for 42 structured features |
| `engine/models/v2/diagnostic_all60_*` | Retained provisional all-60 diagnostic experiment artifacts |
