# MEDHA V2 STEP 2 — DATASET AUDIT

## 1. Executive Summary

The regenerated dataset `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx` is a well-structured, 11-sheet workbook containing 30,000 longitudinal rows across 1,000 victims × 30 timepoints. DDS is a continuous target in [0, 84.66] with mean ≈ 40, generated from **same-timepoint observations only** with ±15% weight jitter and SD=7 Gaussian noise. This is a **critical improvement over the old dataset**, where the six-variable lag reconstruction achieved R²=1.0. In the regenerated dataset, the lag reconstruction R² is only **0.5333**, and the DDS–target correlation is 0.31, confirming DDS is not deterministically derived.

All four modalities (Structured, Text, Voice, Behaviour) carry genuine signal for DDS prediction (R² from 0.47 to 0.67 individually, 0.74 combined). Missingness is fully governed by availability flags. The dataset is ready for V2 implementation.

---

## 2. Workbook Inventory

| Sheet | Rows | Cols | Purpose |
|---|---|---|---|
| **Longitudinal_Data** | 30,000 | 83 | Primary ML dataset |
| **Victim_Profiles** | 1,000 | 14 | Static victim demographics / trajectory types |
| **Case_Events** | 7,216 | 5 | Discrete case events (hearings, threats, etc.) |
| **Therapist_Events** | 389 | 11 | Rare therapist observations / interventions |
| **Data_Dictionary** | 83 | 5 | Column metadata with Category, Can_Be_Missing, Used_By_Model |
| **ML_Split_Guide** | 3 | 3 | Split proportions: 70/15/15 by Victim_ID |
| **Target_Definition** | 3 | 3 | DDS and Future_Escalation_Label definitions |
| **Generation_Methodology** | 6 | 2 | How data was generated (profiles → latent trajectory → observations → derived features → target) |
| **Quality_Checks** | 21 | 4 | Pre-computed validation statistics |
| **Demo_Cases** | 180 | 83 | 6 example victims × 30 timepoints |
| **Research_Mapping** | 8 | 4 | Research literature justification |

---

## 3. Longitudinal Structure

| Metric | Value |
|---|---|
| Total rows | 30,000 |
| Unique Victim_IDs | 1,000 |
| Rows per victim | 30 (all identical) |
| Timepoints per victim | 30 (1–30, no gaps) |
| Duplicate Victim_ID + Timepoint | 0 |
| Victims with >1 Case_ID | 0 (1:1 mapping) |
| Timepoints monotonically increasing | Yes |
| Date_Time column | Present, datetime64 |

**Conclusion:** Perfect balanced panel. Every victim has exactly 30 observations at timepoints 1–30. No duplicates, no gaps.

---

## 4. DDS Target Definition

### From `Target_Definition` sheet:
- `Future_Escalation_Label`: "1 = simulated predefined escalation during next 7 timepoints; 0 = none; final 7 rows unavailable"
- Prediction input: "Information available through current timepoint T only"
- Clinical status: "Non-clinical synthetic outcome — Not validated"

### From `Generation_Methodology` sheet:
The generation pipeline is:
1. **Profiles** → Fixed victim/case/protective profiles
2. **Latent trajectory** → Stochastic temporal process with trajectory types and event shocks
3. **Observations** → Noisy structured, behavioural, text, voice, diary, and professional signals
4. **Derived features** → Past/current observations only
5. **Target** → "Hidden future state/context process, **not a DDS threshold**"
6. **Validation** → Missingness, range, duplicate, temporal, and leakage checks

### From `Quality_Checks` sheet:
- **"Generation basis"**: "Same-timepoint observations only; no Previous_DDS/Rolling_DDS_Mean/DDS_Slope/Recent_Change_Rate used to generate DDS"
- **Weight jitter**: "Independent uniform ±15% per row and component"
- **Gaussian noise**: "SD = 7 DDS points"
- **Six-variable reconstruction R² (test)**: **0.5552**
- **Non-lag structured/behaviour reconstruction R² (test)**: 0.6366

### DDS Statistics:
| Statistic | Value |
|---|---|
| Non-null | 30,000 / 30,000 (100%) |
| Range | [0.00, 84.66] |
| Mean | 39.98 |
| Median | 40.20 |
| Std dev | 13.04 |
| P5 | 18.41 |
| P25 | 30.57 |
| P75 | 49.45 |
| P95 | 60.95 |
| Unique values | 5,817 |

DDS is **continuous** (5,817 unique values over 30,000 rows), roughly normally distributed, always available. It drifts upward over time: mean DDS at T=1 is ≈34.7, at T=30 is ≈44.7, consistent with the mixed trajectory types.

---

## 5. DDS Leakage Audit

### Key Question: Can DDS be reconstructed from other columns?

**Six-variable lag reconstruction R² = 0.5333** (vs R²=1.0 in old dataset). This confirms the regenerated dataset has successfully broken the deterministic dependency.

| Feature | Pearson with DDS | R² (univariate) | Type | Leakage Risk |
|---|---|---|---|---|
| `Rolling_DDS_Mean` | 0.7244 | 0.5248 | DERIVED from past DDS | **LEAKY for current DDS** |
| `DDS_Deviation_From_Baseline` | 0.7526 | 0.5664 | DERIVED (DDS - Baseline_DDS) | **LEAKY for current DDS** |
| `Recent_Max_DDS` | 0.6864 | 0.4711 | DERIVED from past DDS | **LEAKY for current DDS** |
| `Recent_Min_DDS` | 0.6679 | 0.4461 | DERIVED from past DDS | **LEAKY for current DDS** |
| `Previous_DDS` | 0.6366 | 0.4052 | DERIVED from past DDS | **LEAKY for current DDS** |
| `Baseline_DDS` | 0.5632 | 0.3172 | DERIVED (static per victim) | Borderline — see below |
| `Delta_DDS` | 0.4298 | 0.1848 | DERIVED (DDS - Previous_DDS) | **LEAKY for current DDS** |
| `Rolling_DDS_SD` | 0.0634 | 0.0040 | DERIVED from past DDS | **LEAKY for current DDS** |
| `DDS_Slope` | 0.0442 | 0.0020 | DERIVED from past DDS | **LEAKY for current DDS** |
| `Recent_Change_Rate` | 0.0293 | 0.0009 | DERIVED from past DDS | **LEAKY for current DDS** |

### Baseline_DDS Assessment:
`Baseline_DDS` is **constant per victim** (confirmed: 100% of victims have a single value). It represents the victim's initial distress level. It has r=0.56 with DDS. This is a **victim-level trait feature**, not derived from the current DDS being predicted. However, it is computed from the generation process's initial DDS value. For the **strictest anti-leakage interpretation**, it should be excluded from DDS models because it is mathematically derived from the target distribution. For the GRU it is legitimate.

### DDS_Deviation_From_Baseline:
This is `DDS - Baseline_DDS`. Since it includes the current DDS value, it is **definitely leaky** (r=0.7526).

---

## 6. Temporal Availability Audit

| Feature | Available at T? | Uses past DDS? | Uses current DDS? | Uses future data? | Allowed for current DDS model? |
|---|---|---|---|---|---|
| `Previous_DDS` | Yes (shifted) | ✅ Yes (T-1) | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Rolling_DDS_Mean` | Yes (window) | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Rolling_DDS_SD` | Yes (window) | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `DDS_Slope` | Yes (window) | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Recent_Change_Rate` | Yes | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Recent_Max_DDS` | Yes (window) | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Recent_Min_DDS` | Yes (window) | ✅ Yes | ❌ No | ❌ No | ❌ **No** — target-derived historical |
| `Delta_DDS` | Yes | ✅ Yes (T-1) | ✅ Yes | ❌ No | ❌ **No** — contains current DDS |
| `DDS_Deviation_From_Baseline` | Yes | ❌ No | ✅ Yes | ❌ No | ❌ **No** — contains current DDS |
| `Baseline_DDS` | Yes (static) | ❌ No | ❌ No | ❌ No | ⚠️ Borderline — see Section 5 |
| `Baseline_Response_Delay` | Yes (static) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Baseline_Engagement` | Yes (static) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Baseline_Text_Distress` | Yes (static) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Baseline_Voice_Distress` | Yes (static) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Baseline_Checkin_Distress` | Yes | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Text_Distress_Deviation` | Yes | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Voice_Distress_Deviation` | Yes | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Behaviour_Trend` | Yes (window) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Engagement_Trend` | Yes (window) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Text_Distress_Trend` | Yes (window) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Voice_Distress_Trend` | Yes (window) | ❌ No | ❌ No | ❌ No | ✅ Yes |
| `Future_Escalation_Label` | ❌ Future | ❌ No | ❌ No | ✅ Yes | ❌ **No** — future target |

---

## 7. Modality Feature Mapping

### STRUCTURED (Case/Clinical/Context)
| Feature | Pearson w/ DDS | Missing% | Notes |
|---|---|---|---|
| `Case_Type` | — | 0% | Categorical (6 values) |
| `Case_Stage` | — | 0% | Categorical |
| `Mood` | −0.631 | 10.2% | ✅ Strong signal, missing when Checkin_Available=0 |
| `Stress` | 0.639 | 10.2% | ✅ Strong signal |
| `Sleep` | −0.598 | 10.2% | ✅ |
| `Functioning` | −0.588 | 10.2% | ✅ |
| `Safety` | −0.614 | 10.2% | ✅ |
| `Social_Support_Checkin` | 0.010 | 10.2% | ⚠️ Near-zero signal |
| `Self_Reported_Wellbeing` | −0.585 | 10.2% | ✅ |
| `Threat_Event` | — | 0% | Binary event |
| `Upcoming_Hearing` | — | 0% | Binary event |
| `Hearing_Completed` | — | 0% | Binary event |
| `Investigation_Delay` | — | 0% | Binary event |
| `Compensation_Delay` | — | 0% | Binary event |
| `Relocation_Stress` | — | 0% | Binary event |
| `Rehabilitation_Issue` | — | 0% | Binary event |
| `Protection_Event` | — | 0% | Binary event |
| `Family_Support` | — | 0% | Continuous |
| `Social_Support` | — | 0% | Continuous |
| `Therapist_Engagement` | — | 0% | Continuous |
| `Access_To_Services` | — | 0% | Continuous |
| `Stable_Housing` | — | 0% | Continuous |
| `Other_Protective_Factors` | — | 0% | Continuous |
| `Recent_Episode` | — | 0% | Binary (derived) |
| `Episode_Severity` | — | 99.3% | Categorical (Low/Moderate/High), very sparse |
| `Family_Reported_Episode` | — | 0% | Binary |

**Structured-only Linear R² = 0.6694** (n=26,955, 27 features)

### TEXT
| Feature | Pearson w/ DDS | Missing% | Availability |
|---|---|---|---|
| `Text_Distress` | 0.748 | 26.0% | When `Text_Available`=1 |
| `Fear` | 0.739 | 26.0% | When `Text_Available`=1 |
| `Threat_Context` | 0.096 | 26.0% | ⚠️ Weak signal |
| `Negative_Affect` | 0.729 | 26.0% | When `Text_Available`=1 |
| `Urgency` | 0.742 | 26.0% | When `Text_Available`=1 |
| `Diary_Length` | −0.009 | 81.2% | When `Diary_Available`=1; ⚠️ no signal |
| `Diary_Distress_Feature` | 0.661 | 81.2% | When `Diary_Available`=1 |

**No raw text** is present in the dataset. Text features are pre-computed numeric signals.
**Text-only Linear R² = 0.6345** (n=22,195, 5 features)
`Text_Available` rate: 74.0% (22,195 / 30,000)

### VOICE
| Feature | Pearson w/ DDS | Missing% | Availability |
|---|---|---|---|
| `Voice_Distress` | 0.769 | 63.3% | When `Voice_Available`=1 |
| `Pause_Ratio` | 0.706 | 63.3% | When `Voice_Available`=1 |
| `Speech_Rate_Deviation` | 0.748 | 63.3% | When `Voice_Available`=1 |
| `Energy_Deviation` | 0.729 | 63.3% | When `Voice_Available`=1 |
| `Acoustic_Indicator` | 0.726 | 63.3% | When `Voice_Available`=1 |

**No raw audio** is present. Voice features are pre-computed.
**Voice-only Linear R² = 0.6413** (n=10,995, 5 features)
`Voice_Available` rate: 36.6% (10,995 / 30,000)

### BEHAVIOUR
| Feature | Pearson w/ DDS | Missing% | Notes |
|---|---|---|---|
| `Engagement_Score` | −0.669 | 0% | ✅ Strong signal |
| `Engagement_Deviation` | −0.617 | 0% | ✅ Strong signal |
| `Missed_Checkin` | 0.003 | 0% | ⚠️ Near-zero signal |
| `Response_Delay_Hours` | 0.302 | 0% | Moderate |
| `Response_Delay_Deviation` | 0.291 | 0% | Moderate |
| `Session_Duration_Minutes` | −0.049 | 0% | ⚠️ Weak |
| `Interaction_Frequency_7d` | −0.094 | 0% | ⚠️ Weak |

**Behaviour-only Linear R² = 0.4690** (n=30,000, 7 features)
Always available (no missingness).

---

## 8. Future-Label Audit

| Column | Purpose | Use for DDS? | Use for GRU? |
|---|---|---|---|
| `DDS` | **Target** for current DDS prediction | TARGET | Input (historical) |
| `Future_Escalation_Label` | Binary future escalation (next 7 timepoints) | ❌ Never | TARGET |
| `Intervention` | Post-hoc intervention type | ❌ Never (93.9% missing) | ⚠️ Caution |
| `Follow_Up` | Post-hoc follow-up outcome | ❌ Never (94.2% missing) | ⚠️ Caution |

`Future_Escalation_Label` is NaN for timepoints 24–30 (7,000 rows = 23.3%). This is by design: the label looks 7 timepoints ahead, and the last 7 timepoints cannot have a valid forward-looking label.

---

## 9. Missing Data Analysis

### By Modality:
| Modality | Availability Flag | Available Rows | Missing % |
|---|---|---|---|
| Checkin (questionnaire) | `Checkin_Available` | 26,955 | 10.2% |
| Text | `Text_Available` | 22,195 | 26.0% |
| Voice | `Voice_Available` | 10,995 | 63.3% |
| Diary | `Diary_Available` | 5,633 | 81.2% |
| Therapist Observation | `Therapist_Observation_Available` | 3,428 | 88.6% |

**Missingness is perfectly systematic**: When `availability_flag = 0`, all sub-features are NaN. When `availability_flag = 1`, zero missingness. This is by design (modality availability simulation).

### Temporal/Derived Missing:
| Feature | Missing | Reason |
|---|---|---|
| `Previous_DDS` | 1,000 (3.3%) | NaN at T=1 (no prior timepoint) |
| `Delta_DDS` | 1,000 | NaN at T=1 |
| `Rolling_DDS_Mean` | 1,000 | NaN at T=1 |
| `DDS_Slope` | 2,000 (6.7%) | NaN at T=1, T=2 (needs ≥3 points) |
| `Behaviour_Trend` | 2,000 | NaN at T=1, T=2 |
| `Future_Escalation_Label` | 7,000 (23.3%) | NaN at T=24–30 (7-step lookahead) |

---

## 10. Target Distributions

### DDS Distribution:
- Continuous, 5,817 unique values over 30,000 rows
- Approximately normal, range [0.00, 84.66]
- Mean = 39.98, Median = 40.20, Std = 13.04
- Drifts upward over time (T=1 mean ≈ 34.7 → T=30 mean ≈ 44.7)

### Future_Escalation_Label Distribution:
- 23,000 non-null values
- Class 0: 21,389 (93.0%)
- Class 1: 1,611 (7.0%)
- Imbalanced (7% positive rate)

---

## 11. Victim-Level Data Quality

- All 1,000 victims have exactly 30 rows and 30 unique timepoints.
- Zero duplicate Victim_ID + Timepoint combinations.
- 1:1 Victim_ID → Case_ID mapping.
- 8 trajectory types distributed across victims: stable (198), gradual_deterioration (178), gradual_recovery (148), fluctuating (128), event_triggered_deterioration (110), resilient (85), event_triggered_recovery (77), rapid_deterioration (76).
- DDS upward drift by timepoint is expected and consistent with trajectory types.
- No impossible transitions or identical trajectories detected.

---

## 12. Data Dictionary Consistency

The `Data_Dictionary` sheet has 83 rows matching the 83 columns in `Longitudinal_Data`. All column names match. Key classifications from `Data_Dictionary`:

- **Category = SIMULATED**: Raw features generated by the simulation
- **Category = DERIVED**: Computed from other columns (baselines, deviations, trends, rolling stats)
- **`Used_By_Model` = "GRU only"**: Explicitly flagged for 4 features: `Previous_DDS`, `Rolling_DDS_Mean`, `DDS_Slope`, `Recent_Change_Rate`

The Data Dictionary correctly flags DDS-derived lag features as "GRU only", which aligns with our leakage rules.

---

## 13. Generation Methodology Findings

The DDS generation pipeline is:
1. **Latent trajectory** → Stochastic process creates an underlying distress path per victim
2. **Same-timepoint observations** → Noisy signals derived from the latent state
3. **DDS** → Generated from same-timepoint observations with ±15% weight jitter + SD=7 noise
4. **Historical/derived features** → Computed AFTER DDS (rolling means, slopes, etc.)
5. **Future_Escalation_Label** → "Hidden future state/context process, NOT a DDS threshold"

**Critical finding from Quality_Checks:** "Same-timepoint observations only; no Previous_DDS/Rolling_DDS_Mean/DDS_Slope/Recent_Change_Rate used to generate DDS."

This means DDS is generated from the same structured/text/voice/behaviour signals that we will use as features, with noise. This is the intended design — each modality contributes genuine (noisy) information about the current distress state.

---

## 14. Final Feature Classification

### A. SAFE FOR CURRENT DDS PREDICTION
`Case_Type`, `Case_Stage`, `Checkin_Available`, `Mood`, `Stress`, `Sleep`, `Functioning`, `Safety`, `Social_Support_Checkin`, `Self_Reported_Wellbeing`, `Response_Delay_Hours`, `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Deviation`, `Threat_Event`, `Upcoming_Hearing`, `Hearing_Completed`, `Investigation_Delay`, `Compensation_Delay`, `Relocation_Stress`, `Rehabilitation_Issue`, `Protection_Event`, `Family_Support`, `Social_Support`, `Therapist_Engagement`, `Access_To_Services`, `Stable_Housing`, `Other_Protective_Factors`, `Text_Available`, `Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`, `Voice_Available`, `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`, `Diary_Available`, `Diary_Length`, `Diary_Distress_Feature`, `Therapist_Observation_Available`, `Therapist_Observation_Score`, `Recent_Episode`, `Episode_Severity`, `Family_Reported_Episode`, `Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Text_Distress`, `Baseline_Voice_Distress`, `Baseline_Checkin_Distress`, `Text_Distress_Deviation`, `Voice_Distress_Deviation`, `Behaviour_Trend`, `Engagement_Trend`, `Text_Distress_Trend`, `Voice_Distress_Trend`, `Discordance_Test_Feature`, `Discordance_Example_Flag`

### B. BORDERLINE (Exclude from DDS models to be safe)
`Baseline_DDS` — Constant per victim, derived from the generation process's initial DDS. Not derived from the row's DDS, but correlated (r=0.56). Safer to exclude.

### C. DEFINITELY LEAKY (Exclude from current DDS models)
`Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Recent_Change_Rate`, `Recent_Max_DDS`, `Recent_Min_DDS`, `Delta_DDS`, `DDS_Deviation_From_Baseline`

### D. HISTORICAL/TEMPORAL (Valid for GRU temporal model only)
All features in category C above, plus `Baseline_DDS`, `Trajectory_State`

### E. TARGET / LABEL
`DDS` (current DDS target), `Future_Escalation_Label` (GRU target)

### F. ID / METADATA
`Victim_ID`, `Case_ID`, `Timepoint`, `Date_Time`

### G. POST-HOC / OUTCOME (Exclude from prediction models)
`Intervention`, `Follow_Up`

---

## 15. Recommended Feature Groups

### Structured DDS Model
`Case_Type`, `Case_Stage`, `Mood`, `Stress`, `Sleep`, `Functioning`, `Safety`, `Social_Support_Checkin`, `Self_Reported_Wellbeing`, `Response_Delay_Hours`, `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Deviation`, `Threat_Event`, `Upcoming_Hearing`, `Hearing_Completed`, `Investigation_Delay`, `Compensation_Delay`, `Relocation_Stress`, `Rehabilitation_Issue`, `Protection_Event`, `Family_Support`, `Social_Support`, `Therapist_Engagement`, `Access_To_Services`, `Stable_Housing`, `Other_Protective_Factors`, `Recent_Episode`, `Episode_Severity`, `Family_Reported_Episode`
**Expected R² ≈ 0.67**

### Text DDS Model
`Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`
Optional additions: `Diary_Distress_Feature` (if diary available)
**Expected R² ≈ 0.63**

### Voice DDS Model
`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`
**Expected R² ≈ 0.64**

### Behaviour DDS Model
`Engagement_Score`, `Engagement_Deviation`, `Missed_Checkin`, `Response_Delay_Hours`, `Response_Delay_Deviation`, `Session_Duration_Minutes`, `Interaction_Frequency_7d`
**Expected R² ≈ 0.47**

### GRU Temporal Model (Future Escalation)
All SAFE features + all HISTORICAL/TEMPORAL features (Previous_DDS, Rolling_DDS_Mean, DDS_Slope, Recent_Change_Rate, etc.)
Must EXCLUDE: `Future_Escalation_Label` (target), `DDS` at the prediction timepoint itself

---

## 16. Open Questions / Unresolved Issues

1. **Baseline_DDS inclusion**: Should it be included in structured DDS models? It's a static per-victim feature (not derived from the row being predicted), but it originates from the DDS generation process. Recommendation: **exclude** to be safe.

2. **Diary and Therapist features**: `Diary_Distress_Feature` (81% missing) and `Therapist_Observation_Score` (89% missing) are highly sparse. Should they be included in models? They may cause bias toward rare-observation rows. Recommendation: **test with and without**.

3. **Behaviour feature overlap**: Some features appear in both Structured and Behaviour categories (`Engagement_Score`, `Response_Delay_Hours`, etc.). Need to decide whether the Behaviour DDS model should use unique features or overlapping ones. Recommendation: **allow overlap** for individual modality evaluation, then use specialist predictions (not raw features) for fusion.

4. **Checkin_Available missingness**: When `Checkin_Available=0`, all 7 questionnaire features are NaN (10.2% of rows). DDS is still available at those timepoints. The structured model must handle this missingness or train only on `Checkin_Available=1` rows.

5. **`Intervention` and `Follow_Up`**: These are post-hoc outcome variables (94% missing). They should be excluded from all prediction models. Are they needed for any downstream triage logic?

6. **`Trajectory_State`**: Categorical (Stable/Deteriorating/Improving/Rapidly_Deteriorating). This is DERIVED and likely computed from DDS trajectory. Should be excluded from DDS models but may be useful for GRU.
