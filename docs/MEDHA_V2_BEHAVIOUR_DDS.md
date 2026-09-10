# MEDHA V2 STEP 8 — BEHAVIOUR DDS SPECIALIST REPORT

## 1. Executive Summary

This report documents the implementation, mathematical verification, training, evaluation, and boundary validation of the **Behaviour DDS Specialist** for MEDHA V2.

The Behaviour DDS Specialist predicts current-timepoint psychological distress (**DDS**) exclusively from longitudinal behavioural interactions, check-in engagement patterns, response latencies, and app usage dynamics.

### Key Accomplishments:
- **Pre-existing Behaviour Engine Preserved**: All legacy Behaviour Engine components (`engine/behaviour_engine/medha_scoring_artifacts.joblib`, `medha_scoring_pipeline_corrected.py`, `medha_scoring_api.py`, `MEDHA_scored_test_set.csv`) remain 100% untouched.
- **Mathematical Deviation Verification**:
  - In the raw dataset (`MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`), `Engagement_Deviation` is signed (ranging from $-0.935$ to $+0.449$, with $74.0\%$ of rows negative). In past fusion prototypes, naive linear summation caused engagement drops to numerically lower distress risk.
  - As mandated by the core Behaviour Engine specification (`MEDHA_Behaviour_Engine_Complete_Summary.md` line 131, `medha_scoring_pipeline_corrected.py` line 90, and `FINAL_MEDHA_FUSION_REPORT.md` line 4), deviation features were mathematically verified and computed as **absolute deviations** ($|z|$), correctly treating behavioral departure from baseline as a distress indicator.
  - Empirical verification confirmed that absolute deviation $|Engagement\_Deviation|$ correlates positively ($+0.5197$) with distress, produces a clinically consistent positive regression weight ($+5.2674$), and outperforms signed deviation on held-out test MAE ($7.3530$ vs $7.3701$).
- **100% Observation Coverage**: Unlike Voice ($36.65\%$) or Text ($74.7\%$), behavioural interaction metadata is recorded for $100\%$ of observations ($30,000 / 30,000$ rows, including all $4,500$ held-out test rows).
- **Leakage-Safe Feature Selection**: Strictly enforces the Step 4 feature policy. All target lags, future labels, text features, voice features, and structured clinical context variables are rejected.
- **Authoritative Split**: Trained solely on the 700 training victims ($21,000$ rows), validated on 150 validation victims ($4,500$ rows), and evaluated out-of-sample on the 150 held-out test victims ($4,500$ rows).
- **Strong Predictive Signal (Canonical Ridge Model)**:
  - **Test $R^2$**: **0.5106** (vs. naïve baseline $R^2 = -0.0039$)
  - **Test MAE**: **7.3530** (vs. naïve baseline MAE = 10.8196, a **+32.04% MAE improvement**)
  - **Test RMSE**: **9.1945** (vs. baseline RMSE = 13.1688)
  - **Test Pearson $r$**: **0.7147**
  - **Test Spearman $\rho$**: **0.7332**
- **Canonical Specialist Designation**: The **All-10 Behaviour Ridge Regressor (Absolute Deviations)** is designated as the **canonical / recommended V2 Behaviour DDS Specialist**, providing an interpretable linear formulation with clinically consistent weights.

---

## 2. Behaviour Engine Lineage & Mathematical Deviation Definition

### A. Architectural Lineage
The Behaviour Engine quantifies changes in victim interaction dynamics (latency, skip rates, session durations, and engagement baseline shifts) that precede psychological escalation:

```text
User Check-In & App Interaction Events
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  Behaviour Signal Processing & State Store             │
│  - Interaction frequency, session duration, latency    │
│  - Personal baseline tracking (μ, σ)                  │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  Standardized Behavioural Outputs in Dataset           │
│  - Engagement_Score          (0-1 app activity index)  │
│  - Engagement_Deviation      (shift relative to base)  │
│  - Response_Delay_Hours      (latency to prompt)       │
│  - Response_Delay_Deviation  (latency shift)           │
│  - Missed_Checkin            (attendance flag: 0/1)    │
│  - Interaction_Frequency_7d  (7-day rolling sessions)  │
│  - Session_Duration_Minutes  (active interaction time) │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  Mathematical Verification & Alignment                 │
│  - |Engagement_Deviation| = abs(Engagement_Deviation)  │
│  - |Response_Delay_Deviation| = abs(Delay_Deviation)   │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  V2 Behaviour DDS Specialist Regression Layer          │
│  y = Intercept + ∑ (w_i * feature_i)                   │
└────────────────────────────────────────────────────────┘
      │
      ▼
Predicted Current-Timepoint DDS
```

### B. Mathematical Verification of Deviation Features

#### 1. The Discrepancy in Raw Synthetic Data
In the regenerated longitudinal spreadsheet, `Engagement_Deviation` was generated as a signed relative change:
$$\text{Engagement\_Deviation} \approx \text{Engagement\_Score} - \text{Baseline\_Engagement}$$
Because victims in psychological distress typically withdraw from check-ins:
- $22,210$ out of $30,000$ rows ($74.0\%$) have negative values ($\text{Engagement\_Deviation} < 0$).
- Raw signed correlation with DDS was $-0.6167$.
- In earlier fusion prototypes (`engine/fusion_engine/compile_report.py`), a naive linear rule:
  $$\text{behaviour\_risk} = 0.4 \cdot 0.5 + 0.3 \cdot \text{Engagement\_Deviation} + 0.3 \cdot \text{Missed\_Checkin}$$
  resulted in a negative correlation ($-0.144$) because dropping engagement subtracted from risk rather than adding to it.

#### 2. The Intended Behaviour Engine Specification
In the core Behaviour Engine design (`engine/behaviour_engine/medha_scoring_pipeline_corrected.py` line 90 and `engine/behaviour_engine/MEDHA_Behaviour_Engine_Complete_Summary.md` line 131):
$$\text{engagement\_deviation} = \text{mean}(|z|)$$
Deviation is explicitly defined as **absolute deviation**, reflecting that **any substantial divergence from a victim's established behavioral equilibrium represents elevated clinical distress**.

#### 3. Empirical Verification Results
Transforming `Engagement_Deviation` and `Response_Delay_Deviation` to absolute values:
- $|\text{Engagement\_Deviation}| \ge 0$ across all 30,000 rows.
- Correlation with DDS: **$+0.5197$** (strongly positive).
- Ridge regression weight: **$+5.2674$** (clinically consistent: greater absolute deviation increases predicted distress).
- Held-out test performance:
  - **Absolute Deviations Model**: Test MAE = **7.3530**, Test $R^2$ = **0.5106**
  - **Signed Deviations Model**: Test MAE = **7.3701**, Test $R^2$ = **0.5089**

The absolute deviation formulation is mathematically verified, empirically superior, and aligns with clinical domain reality.

---

## 3. Exact Behaviour-Derived Features

| Feature Name | Category | Missing % | Correlation with DDS | Description |
|---|---|---|---|---|
| `Engagement_Score` | Core Interaction | 0.00% | -0.6687 | Normalized check-in activity and interaction intensity |
| `Engagement_Deviation` | Core Interaction | 0.00% | +0.5197 (abs) | Absolute deviation from personal baseline engagement |
| `Response_Delay_Hours` | Core Interaction | 0.00% | +0.3023 | Time elapsed from prompt notification to check-in completion |
| `Response_Delay_Deviation` | Core Interaction | 0.00% | +0.2446 (abs) | Absolute deviation from personal baseline response latency |
| `Missed_Checkin` | Core Interaction | 0.00% | +0.0034 | Binary indicator (1 = missed check-in, 0 = completed) |
| `Interaction_Frequency_7d` | Core Interaction | 0.00% | -0.0939 | Cumulative app session count over preceding 7 days |
| `Session_Duration_Minutes` | Core Interaction | 0.00% | -0.0488 | Total minutes spent on the check-in interface |
| `Baseline_Response_Delay` | Extended Longitudinal | 0.00% | +0.1386 | Victim's historical mean response latency |
| `Baseline_Engagement` | Extended Longitudinal | 0.00% | -0.3832 | Victim's historical mean engagement score |
| `Behaviour_Trend` | Extended Longitudinal | 6.67% | -0.1734 | 3-timepoint trajectory slope (imputed on days 1-2) |

---

## 4. Strict Boundary & Leakage Enforcement

The Behaviour Specialist is protected by hard-failing policy validation (`validate_behaviour_specialist_features` in `engine/v2/v2_feature_policy.py`):

1. **Target Feature Rejection**: `DDS`, `Future_Escalation_Label` $\to$ `ValueError`
2. **Target Lag Rejection**: `Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Recent_Change_Rate`, `Delta_DDS`, `Baseline_DDS` $\to$ `ValueError`
3. **Cross-Modal Text Rejection**: `Text_Distress`, `Fear`, `Negative_Affect`, `Urgency`, `Threat_Context`, etc. $\to$ `ValueError`
4. **Cross-Modal Voice Rejection**: `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator` $\to$ `ValueError`
5. **Structured Clinical Context Rejection**: `Mood`, `Stress`, `Sleep`, `Safety`, `Threat_Event`, `Case_Type`, `Recent_Episode` $\to$ `ValueError`
6. **Metadata & Post-Hoc Rejection**: `Victim_ID`, `Case_ID`, `Timepoint`, `Intervention`, `Follow_Up` $\to$ `ValueError`
7. **Duplicate Protection**: Any duplicated feature $\to$ `ValueError`

---

## 5. Authoritative Training & Preprocessing Protocol

- **Split Roster**:
  - **Train**: 700 victims ($21,000$ rows)
  - **Validation**: 150 victims ($4,500$ rows)
  - **Test**: 150 victims ($4,500$ rows)
- **Zero Cross-Victim Leakage**: Victims are strictly partitioned; no victim appears across splits.
- **Preprocessing Purity**: `SimpleImputer(strategy="median")` is fitted strictly on the $21,000$ training observations.
- **Trend Imputation**: Only `Behaviour_Trend` contains missing values (at timepoints 1 and 2 per victim, where 3-day history is unobserved). The train median ($0.0$) is used for deterministic imputation.

---

## 6. Detailed Evaluation Results across Splits

Evaluation metrics were computed across all splits using the fixed victim-level split:

### Held-Out Test Set Results (150 Victims, 4,500 Observations)

| Model Name | Test MAE | Test RMSE | Test $R^2$ | Test Pearson $r$ | Test Spearman $\rho$ | Baseline MAE | MAE Improvement |
|---|---|---|---|---|---|---|---|
| **Ridge (All 10 Absolute) — Canonical** | **7.3530** | **9.1945** | **0.5106** | **0.7147** | **0.7332** | 10.8196 | **+32.04%** |
| **XGBoost (All 10 Absolute)** | 7.2577 | 9.0949 | 0.5211 | 0.7229 | 0.7321 | 10.8196 | **+32.92%** |
| **Ridge (Core 7 Absolute)** | 7.7020 | 9.6546 | 0.4604 | 0.6785 | 0.6965 | 10.8196 | **+28.81%** |
| **XGBoost (Core 7 Absolute)** | 7.5827 | 9.5193 | 0.4754 | 0.6896 | 0.6976 | 10.8196 | **+29.92%** |
| **Ridge (All 10 Signed) — Diagnostic** | 7.3701 | 9.2107 | 0.5089 | 0.7135 | 0.7304 | 10.8196 | **+31.88%** |
| **XGBoost (All 10 Signed) — Diagnostic** | 7.2736 | 9.1042 | 0.5202 | 0.7221 | 0.7316 | 10.8196 | **+32.77%** |

### Complete Multi-Split Performance (Canonical Ridge Model)

| Split | Sample Size | MAE | RMSE | $R^2$ | Pearson $r$ | Spearman $\rho$ | Baseline MAE | MAE Improvement |
|---|---|---|---|---|---|---|---|---|
| **Train** | 21,000 | 7.4401 | 9.3320 | 0.4900 | 0.7000 | 0.7172 | 10.6962 | **+30.44%** |
| **Validation** | 4,500 | 7.2715 | 9.1091 | 0.4913 | 0.7029 | 0.7188 | 10.4499 | **+30.41%** |
| **Test** | 4,500 | 7.3530 | 9.1945 | 0.5106 | 0.7147 | 0.7332 | 10.8196 | **+32.04%** |

The specialist exhibits **no apparent overfitting / stable held-out performance**, with test MAE ($7.3530$) matching train MAE ($7.4401$) and test $R^2$ ($0.5106$) exceeding train $R^2$ ($0.4900$).

---

## 7. Canonical Ridge Formulation & Feature Importance

### A. Mathematical Regression Equation
The canonical specialist predicts continuous DDS using the following regularized linear formulation:

$$\begin{aligned}
\text{DDS} = 72.7589 &- 42.8463 \cdot \text{Engagement\_Score} \\
&+ 40.5461 \cdot \text{Behaviour\_Trend} \\
&- 14.2674 \cdot \text{Baseline\_Engagement} \\
&+ 5.2674 \cdot |\text{Engagement\_Deviation}| \\
&+ 0.4290 \cdot \text{Response\_Delay\_Hours} \\
&- 0.3400 \cdot \text{Missed\_Checkin} \\
&- 0.3246 \cdot \text{Baseline\_Response\_Delay} \\
&+ 0.0625 \cdot \text{Interaction\_Frequency\_7d} \\
&- 0.0492 \cdot |\text{Response\_Delay\_Deviation}| \\
&+ 0.0221 \cdot \text{Session\_Duration\_Minutes}
\end{aligned}$$

### B. Clinical Interpretation of Coefficients
- **Engagement Score ($-42.85$)**: Robust active engagement is the strongest protective indicator against acute psychological distress.
- **Behaviour Trend ($+40.55$)**: A worsening trajectory slope over consecutive days strongly indicates accumulating distress.
- **Baseline Engagement ($-14.27$)**: High personal baseline engagement reflects protective emotional resilience.
- **Absolute Engagement Deviation ($+5.27$)**: Erratic or substantial departures from personal baseline reflect behavioural instability and distress.
- **Response Delay Hours ($+0.43$)**: Increasing latency to respond to prompts indicates emotional fatigue, withdrawal, or avoidance.

### C. Feature Importance Table

| Feature | Ridge Coefficient | XGBoost Gain Importance | Clinical Role |
|---|---|---|---|
| `Engagement_Score` | -42.8463 | 0.4939 | Primary protective engagement index |
| `Engagement_Deviation` | +5.2674 | 0.1472 | Behavioral instability indicator |
| `Response_Delay_Hours` | +0.4290 | 0.1248 | Avoidance / withdrawal latency |
| `Behaviour_Trend` | +40.5461 | 0.0984 | Short-term trajectory deterioration |
| `Baseline_Engagement` | -14.2674 | 0.0631 | Personal protective resilience baseline |
| `Baseline_Response_Delay` | -0.3246 | 0.0289 | Personal latency baseline |
| `Interaction_Frequency_7d` | +0.0625 | 0.0163 | Longitudinal check-in cadence |
| `Session_Duration_Minutes` | +0.0221 | 0.0135 | Time on interface |
| `Response_Delay_Deviation` | -0.0492 | 0.0094 | Latency variance |
| `Missed_Checkin` | -0.3400 | 0.0045 | Binary check-in absence |

---

## 8. Cross-Specialist Comparison on Held-Out Test Set (150 Victims)

All 4 independent specialist engines have now been constructed and evaluated on the identical 150 test victims:

| Specialist Engine | Features Used | Evaluated Rows | Test MAE | Test RMSE | Test $R^2$ | Pearson $r$ | MAE Improvement |
|---|---|---|---|---|---|---|---|
| **Structured DDS (Step 5)** | 42 structured | 4,500 (100%) | **6.1611** | **7.8184** | **0.6536** | **0.8087** | **+45.17%** |
| **Voice DDS (Step 7)** | 5 acoustic | 1,692 (37.6%) | **6.3070** | **7.9104** | **0.6529** | **0.8082** | **+43.23%** |
| **Text DDS (Step 6)** | 5 MuRIL text | 3,362 (74.7%) | **6.4352** | **8.0783** | **0.6365** | **0.7978** | **+41.53%** |
| **Behaviour DDS (Step 8)** | 10 behavioural | 4,500 (100%) | **7.3530** | **9.1945** | **0.5106** | **0.7147** | **+32.04%** |

### Key Cross-Specialist Insights:
1. **Complementary Modalities**: Structured, Voice, and Text specialists capture explicit and expressive distress signals ($R^2 \approx 0.64 - 0.65$), while the Behaviour specialist captures passive interaction patterns ($R^2 = 0.5106$).
2. **Universal Availability**: Behaviour and Structured specialists provide $100\%$ temporal availability ($4,500$ rows), ensuring continuous distress tracking even when a victim chooses not to speak (Voice missing in $62.4\%$ of test rows) or write (Text missing in $25.3\%$ of test rows).
3. **Zero Contamination**: Each specialist adheres strictly to its own domain inputs with zero feature overlap across modalities.

---

## 9. Artifact Inventory & Verification

### A. Saved Model Files
Persisted in both `models/behaviour_dds_v2/` and `engine/models/behaviour_dds_v2/`:
- `v2_behaviour_dds_ridge_all10.pkl` (Canonical specialist)
- `v2_behaviour_dds_xgb_all10.json` (Nonlinear baseline)
- `v2_behaviour_dds_ridge_core7.pkl` (Core 7 interaction model)
- `v2_behaviour_dds_xgb_core7.json` (Core 7 XGBoost model)
- `v2_behaviour_dds_diagnostic_signed.json` (Signed deviation diagnostic ablation)
- `v2_behaviour_dds_preprocessor.pkl` (Fitted SimpleImputer)
- `v2_behaviour_dds_features.json` (Feature metadata, coefficients, and intercept)
- `v2_behaviour_dds_metrics.json` (Complete multi-split evaluation metrics)
- `v2_behaviour_dds_importance.csv` (Coefficients and gain importances)

### B. Saved Prediction Outputs
Persisted in both `outputs/dds_v2/behaviour/` and `engine/outputs/dds_v2/behaviour/`:
- `test_behaviour_dds_predictions.csv` ($4,500$ test observations with actual DDS, Ridge predictions, and XGBoost predictions)
- `val_behaviour_dds_predictions.csv` ($4,500$ validation observations)

### C. Automated Test Verification
Automated test suite [test_v2_behaviour_dds.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/tests/test_v2_behaviour_dds.py) was executed with full suite:
```bash
pytest engine/tests -v
```
**Result**: **37 passed** in 5.33 seconds (7 Behaviour, 7 Voice, 6 Text, 6 Structured, 11 Feature Policy).

---

## 10. Conclusion & Next Steps

Step 8 (Behaviour DDS Specialist) is complete, mathematically verified, tested, and documented.

All four unimodal specialist engines (Structured, Text, Voice, Behaviour) are now operational and validated under the centralized Step 4 feature policy.

Ready for next instructions (e.g. Multimodal Fusion Engine integration).
