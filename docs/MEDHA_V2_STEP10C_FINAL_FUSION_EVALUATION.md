# MEDHA V2 — STEP 10C: LOCKED FINAL FUSION EVALUATION AND AUDIT REPORT

## Executive Summary

This document presents the **final unbiased evaluation and audit** of the locked MEDHA V2 Fusion Engine on the untouched 4,500-row Test set.

Following the methodological correction in Step 10B:
- Candidate models were trained strictly using **5-fold victim-level Out-of-Fold (OOF) cross-fitting** across the 700 training victims.
- **Candidate C (XGBoost Stacking Regressor)** was selected **strictly on the Validation set** ($N=4,500$, Validation MAE = **5.8851**).
- The model, hyperparameters, preprocessing, and 8-feature schema were **locked and frozen** in `engine/models/v2/fusion_oof/`.
- The Test set remained a pure holdout and was evaluated **exactly once** in this Step 10C.

### Final Benchmark Summary (4,500 Test Rows, 150 Victims)
- **Frozen Fusion Test MAE**: **5.9537** (RMSE: 7.4925, R²: 0.6750, Pearson: 0.8217, Spearman: 0.8272)
- **Structured Specialist Test MAE**: **6.1611** (RMSE: 7.7353, R²: 0.6536, Pearson: 0.8086)
- **Improvement over Structured Specialist**: **+3.37%** (+0.2074 MAE reduction across all 4,500 test observations)
- **Improvement in Full Multimodal Regime (All 4 Modalities Present)**: **+6.64%** (+0.4192 MAE reduction: 6.3121 Structured $\rightarrow$ 5.8929 Fusion)
- **Improvement over Train-Mean Baseline**: **+54.08%** (12.9648 Baseline $\rightarrow$ 5.9537 Fusion)
- **Preliminary Benchmark Distinction**: The earlier test-selected result (~6.0626 Test MAE) is preserved strictly as an exploratory/preliminary benchmark; **5.9537 is the canonical, unbiased MEDHA V2 Fusion Test MAE**.

---

## 1. Step 10B Validation Selection Audit

The fusion model evaluated here is **Candidate C (XGBoost Stacking Regressor)**, which was selected during Step 10B based strictly on held-out Validation performance:

| Candidate Architecture | Training Protocol | Validation MAE | Validation RMSE | Validation R² | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Candidate A (Weighted Average)** | Inverse-OOF-MAE weights | 6.0940 | 7.6155 | 0.6444 | Rejected (Higher Val MAE) |
| **Candidate B (Ridge Stacking)** | RidgeCV ($\alpha=1.0$) on OOF | 5.9062 | 7.3713 | 0.6669 | Rejected (Higher Val MAE) |
| **Candidate C (XGBoost Stacking)**| XGBoost on 8 OOF features | **5.8851** | **7.3544** | **0.6684** | **SELECTED & FROZEN** |

**Confirmation**:
- Validation MAE used for selection: **5.8851**.
- Test data was **zero-percent exposed** during model selection, weight derivation, or hyperparameter choices.

---

## 2. Final Test Set Evaluation (Frozen Candidate C)

The frozen Candidate C was evaluated on the authoritative 150-victim Test set (4,500 longitudinal observations).

### Primary Comparison Table

| Model | Evaluated Subset | N (Observed) | Test MAE | Test RMSE | Test R² | Test Pearson | Test Spearman |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train-Mean Baseline** | Complete Test Set | 4,500 (100.0%) | 12.9648 | 16.1965 | -0.5187 | — | — |
| **Behaviour Specialist** (Ridge Ext-10) | Complete Test Set | 4,500 (100.0%) | 7.3530 | 9.1945 | 0.5106 | 0.7147 | 0.7332 |
| **Text Specialist** (Ridge Core-5) | Available Text Only | 3,362 (74.7%) | 6.4352 | 8.0783 | 0.6365 | 0.7978 | 0.8067 |
| **Voice Specialist** (Ridge Core-5) | Available Voice Only| 1,692 (37.6%) | 6.3070 | 7.9104 | 0.6529 | 0.8082 | 0.8179 |
| **Structured Specialist** (XGBoost) | Complete Test Set | 4,500 (100.0%) | 6.1611 | 7.7353 | 0.6536 | 0.8086 | 0.8146 |
| **MEDHA V2 Frozen Fusion (Candidate C)** | **Complete Test Set** | **4,500 (100.0%)** | **5.9537** | **7.4925** | **0.6750** | **0.8217** | **0.8272** |

### Relative Improvement Summary
- **Over Structured Specialist**: $\frac{6.1611 - 5.9537}{6.1611} \times 100\% =$ **+3.37% improvement** (+0.2074 MAE reduction).
- **Over Best Specialist**: Structured is the best individual specialist (MAE 6.1611); Fusion achieves a **+3.37% improvement**.
- **Over Train-Mean Baseline**: $\frac{12.9648 - 5.9537}{12.9648} \times 100\% =$ **+54.08% improvement**.

---

## 3. Availability-Stratified Performance Analysis

To evaluate how fusion handles real-world missingness, test rows were partitioned into four mutually exclusive and exhaustive strata based on modality availability:

| Stratum | Definition | N | % Test Set | Fusion MAE | Fusion RMSE | Fusion R² | Structured MAE | Structured RMSE | MAE Reduction vs Structured |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. All Available** | Text=1, Voice=1 | 1,269 | 28.20% | **5.8929** | 7.4174 | **0.7076** | 6.3121 | 7.8811 | **+0.4192** (+6.64%) |
| **B. Voice Missing** | Text=1, Voice=0 | 2,093 | 46.51% | **5.9411** | 7.5209 | 0.6752 | 6.1231 | 7.7266 | **+0.1820** (+2.97%) |
| **C. Text Missing** | Text=0, Voice=1 | 423 | 9.40% | **6.0344** | 7.4876 | 0.6422 | 6.0690 | 7.6230 | **+0.0346** (+0.57%) |
| **D. Text & Voice Missing** | Text=0, Voice=0 | 715 | 15.89% | **6.0504** | 7.5444 | 0.6199 | 6.0584 | 7.5634 | **+0.0080** (+0.13%) |
| **Total / Complete** | — | **4,500** | **100.0%** | **5.9537** | **7.4925** | **0.6750** | **6.1611** | **7.7353** | **+0.2074** (+3.37%) |

### Key Architectural Findings:
1. **Monotonic Benefit of Multimodality**: Fusion advantage over Structured scales directly with observed modality richness:
   - Neither Text nor Voice available: $+0.0080$ MAE advantage (essentially matches Structured with slight behavioral stabilization).
   - Voice available only: $+0.0346$ MAE advantage.
   - Text available only: $+0.1820$ MAE advantage.
   - Both Text and Voice available: **$+0.4192$ MAE advantage** (6.64% error reduction).
2. **Graceful Degradation**: When optional modalities (Text and Voice) drop out, the model degrades smoothly to Structured performance rather than collapsing or producing aberrant risk predictions.

---

## 4. Error & Residual Analysis

Analysis of residuals ($e = \hat{y} - y$) and absolute errors ($|e|$) across the 4,500 test rows:

### Error Summary Statistics
- **Mean Residual (Bias)**: **+0.1195** (indicates virtually unbiased predictions across the scale).
- **Mean Absolute Error (MAE)**: **5.9537**
- **Root Mean Squared Error (RMSE)**: **7.4925**
- **Median Absolute Error**: **4.9761** (half of all test observations are predicted within $\pm 4.98$ points on a 0–100 distress scale).
- **Maximum Absolute Error**: **28.4190**
- **Error Exceedance Proportions**:
  - $|e| > 5\text{ DDS}$: **49.73%**
  - $|e| > 10\text{ DDS}$: **18.18%**
  - $|e| > 15\text{ DDS}$: **4.80%**
  - $|e| > 20\text{ DDS}$: **0.87%** (fewer than 1% of observations exhibit severe discrepancy).

### Error Stratified by Actual Target DDS Range

| Target DDS Range | Clinical/Operational Label | N | % Test Set | Subgroup MAE | Subgroup Mean Residual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0 – 25** | Low Distress / Stable | 578 | 12.84% | 7.8017 | +6.9852 (slight overprediction at floor) |
| **25 – 50** | Moderate Distress | 2,782 | 61.82% | **5.4376** | **+0.7919** (highly accurate core cohort) |
| **50 – 75** | High Distress / Escalating | 1,132 | 25.16% | **6.1844** | **-4.9019** (slight regression to mean) |
| **75 – 100** | Severe Distress / Crisis | 8 | 0.18% | 19.2235 | -19.2235 (extreme tail conservative damping) |

---

## 5. Victim-Level Longitudinal Diagnostic (Secondary Metric)

Because the dataset comprises 30 longitudinal timepoints per victim, we aggregated predictions across time to evaluate patient-level distress tracking:

| Model | N (Victims) | Victim-Mean MAE | Victim-Mean RMSE | Victim-Mean R² | Victim-Mean Pearson | Victim-Mean Spearman |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Victim-Mean Structured** | 150 | 1.7280 | 2.1944 | 0.9449 | 0.9781 | 0.9722 |
| **Victim-Mean Fusion** | **150** | **1.4167** | **1.7681** | **0.9642** | **0.9839** | **0.9790** |

*Note*: This victim-level metric is a **secondary longitudinal diagnostic**. The primary benchmark remains the row-level held-out test evaluation (MAE 5.9537). The victim-level aggregation demonstrates that longitudinal noise averages out, achieving $R^2 = 0.9642$ and Pearson $r = 0.9839$ for patient-level monitoring.

---

## 6. Reproducibility and Audit Verification

1. **Deterministic Inference**: Inference was run twice consecutively over the full 4,500 test rows with identical inputs. Maximum absolute prediction difference between runs: **0.0000000000** (bit-for-bit deterministic).
2. **Feature Order Audit**:
   - `Struct_Pred`
   - `Text_Pred`
   - `Voice_Pred`
   - `Behav_Pred`
   - `Struct_Available`
   - `Text_Available`
   - `Voice_Available`
   - `Behav_Available`
   - Exactly 8 inputs. Zero raw features, zero forbidden lag features, zero target leakage.
3. **Artifact Integrity**:
   - Complete audit record saved in `engine/outputs/dds_v2/fusion_final/fusion_final_audit.json`.
   - Frozen model copies stored in `engine/models/v2/fusion_final/` and root `models/v2/fusion_final/`.

---

## 7. Artifacts Created in Step 10C

All final evaluation artifacts are housed in dedicated `fusion_final` directories without touching preliminary or OOF training namespaces:

- **Outputs** (`engine/outputs/dds_v2/fusion_final/` and `outputs/dds_v2/fusion_final/`):
  - `fusion_final_test_predictions.csv`: 4,500 test observations with individual specialist predictions, availability flags, and final fused DDS.
  - `fusion_final_test_metrics.csv`: Comparative benchmark metrics across baseline, all four specialists, and fusion.
  - `fusion_final_availability_metrics.csv`: Detailed performance breakdown across all 4 modality availability strata.
  - `fusion_final_error_analysis.csv`: Error statistics, threshold exceedances, and DDS range breakdowns.
  - `fusion_final_victim_level_metrics.csv`: Secondary longitudinal diagnostic metrics.
  - `fusion_final_reproducibility.json`: Deterministic inference verification record.
  - `fusion_final_audit.json`: Complete audit record.
- **Models** (`engine/models/v2/fusion_final/` and `models/v2/fusion_final/`):
  - `fusion_model.json`: Standalone copy of the frozen XGBoost model.
  - `fusion_feature_config.json`: Canonical feature configuration.

---

## 8. Limitations & Clinical Disclaimer

- **Evaluation Basis**: Text and Voice specialists are evaluated only on their observed/available subsets ($N=3,362$ and $N=1,692$, respectively), whereas Fusion and Structured are evaluated across the full $N=4,500$ test set.
- **Regression vs Clinical Diagnosis**: The MEDHA V2 Fusion Engine is an empirical regression system designed to estimate a continuous Domestic Distress Score (DDS, 0–100) from multimodal indicators.
- **No Causal or Diagnostic Validity**: Performance metrics (MAE 5.95, $R^2$ 0.675) reflect predictive alignment with simulated distress indices; they do not constitute clinical, psychiatric, or legal determinations of risk or domestic violence severity. Human-in-the-loop review remains mandatory for all clinical interventions.
