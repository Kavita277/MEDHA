# MEDHA V2 STEP 6 — TEXT DDS SPECIALIST REPORT

## 1. Executive Summary

This report documents the implementation, training, evaluation, and boundary validation of the **Text DDS Specialist** for MEDHA V2.

The Text DDS Specialist maps unstructured text analysis outputs from the pre-trained MuRIL classifier directly to current-timepoint psychological distress (**DDS**).

### Key Accomplishments:
- **Pre-trained Text Engine Preserved**: The MuRIL weights (`google/muril-base-cased` in `engine/text engine/Models/medha_final_model/`) and inference logic remain 100% intact.
- **Leakage-Safe Feature Selection**: Uses strictly the approved text-derived features from Step 4. All DDS lags, future targets, structured variables, and voice variables are strictly rejected.
- **Authoritative Split**: Trained strictly on the 700 training victims, evaluated out-of-sample on the 150 held-out test victims (3,362 available text rows).
- **Strong Predictive Signal**:
  - **Test $R^2$**: **0.6365** (vs. naïve baseline $R^2 = -0.0039$)
  - **Test MAE**: **6.4352** (vs. naïve baseline MAE = 11.0068, a **+41.53% MAE improvement**)
  - **Test Pearson $r$**: **0.7978**
  - **Test Spearman $\rho$**: **0.8067**
- **Canonical Specialist**: The **Core-5 MuRIL Ridge Regressor** is designated as the **canonical / recommended V2 Text DDS Specialist**, directly translating the 5 MuRIL probability outputs into predicted DDS with positive, clinically consistent weights.
- **Diagnostic Ablation Retained**: The extended 9-feature model is retained strictly as a diagnostic/ablation artifact.

---

## 2. Text Engine & Feature Lineage

The MEDHA Text Engine processes textual inputs (transcribed check-ins, case worker notes, diary entries) through a fine-tuned multilingual MuRIL transformer, outputting 5 sigmoid probabilities:

```text
Raw Text Input
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  MuRIL Multilingual Transformer (5 sigmoid heads)      │
│  Labels: Distress, Fear, Threat, Negative Affect,      │
│          Urgency                                       │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  Standardized Output Vector                            │
│  - Text_Distress    (distress_label)                   │
│  - Fear             (fear_signal)                      │
│  - Threat_Context   (threat_context)                   │
│  - Negative_Affect  (negative_affect)                  │
│  - Urgency          (urgency)                          │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  V2 Text DDS Specialist Regression Layer               │
│  y = Intercept + ∑ (w_i * feature_i)                   │
└────────────────────────────────────────────────────────┘
      │
      ▼
Predicted Current-Timepoint DDS
```

### Exact Text-Derived Features in Regenerated Dataset

| Feature Name | Contract Key in Text Engine | Missing % in Dataset | Pearson $r$ with DDS | Modality Class |
|---|---|---|---|---|
| `Text_Distress` | `text_distress` | 26.02% | 0.748 | Core MuRIL Output |
| `Fear` | `fear_signal` | 26.02% | 0.739 | Core MuRIL Output |
| `Negative_Affect` | `negative_affect` | 26.02% | 0.729 | Core MuRIL Output |
| `Urgency` | `urgency` | 26.02% | 0.742 | Core MuRIL Output |
| `Threat_Context` | `threat_context` | 26.02% | 0.096 | Core MuRIL Output |
| `Baseline_Text_Distress` | *Static victim baseline* | 0.20% | 0.479 | Extended Longitudinal |
| `Text_Distress_Deviation` | *Difference from baseline* | 26.14% | 0.451 | Extended Longitudinal |
| `Text_Distress_Trend` | *Short-term slope* | 36.77% | 0.074 | Extended Longitudinal |
| `Text_Available` | `text_available` (flag) | 0.00% | -0.001 | Modality Availability Flag |

> [!NOTE]
> Text is available in 73.98% of rows (22,195 / 30,000). When a victim skips a check-in or submits no text, `Text_Available = 0` and the text vector values are NaN. The primary evaluation domain for the Text Specialist is rows where text observations were genuinely submitted (`Text_Available == 1`).

---

## 3. Strict Boundary & Leakage Enforcement

The Text Specialist is subject to hard-failing validation (`validate_text_specialist_features` in `engine/v2/v2_feature_policy.py`):

1. **Target Lags Banned**: `Previous_DDS`, `Rolling_DDS_Mean`, `Rolling_DDS_SD`, `DDS_Slope`, `Recent_Change_Rate`, `Delta_DDS`, `Baseline_DDS` are rejected.
2. **Targets Banned**: `DDS`, `Future_Escalation_Label` are rejected.
3. **Structured Modality Banned**: `Mood`, `Stress`, `Sleep`, `Safety`, `Case_Type`, etc., are rejected.
4. **Voice Modality Banned**: `Voice_Distress`, `Pause_Ratio`, `Energy_Deviation`, etc., are rejected.
5. **Metadata Banned**: `Victim_ID`, `Case_ID`, `Timepoint`, `Date_Time`, `Intervention`, `Follow_Up` are rejected.
6. **Zero Duplicates**: Any duplicated feature causes immediate termination.

---

## 4. Authoritative Data Split

Evaluation strictly obeys the Step 3 victim-level split:

| Split | Victims | Total Rows | Available Text Rows (`Text_Available == 1`) | Victim Isolation |
|---|---|---|---|---|
| **Train** | 700 (70%) | 21,000 | 15,493 (73.78%) | Disjoint |
| **Validation** | 150 (15%) | 4,500 | 3,340 (74.22%) | Disjoint |
| **Test** | 150 (15%) | 4,500 | 3,362 (74.71%) | Disjoint |
| **Total** | 1,000 | 30,000 | 22,195 (73.98%) | Zero Overlap |

---

## 5. Model Architecture & Training Details

Two primary model families were implemented and trained on the 15,493 available training observations:

### Model 1: Core 5 MuRIL Ridge Regressor (Canonical / Recommended Text DDS Specialist)
- **Status**: **Canonical Specialist** for MEDHA V2 Text DDS inference.
- **Inputs**: 5 Core MuRIL output features (`Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`).
- **Algorithm**: Regularized Linear Ridge Regression ($\alpha = 1.0$).
- **Advantages**: Fully interpretable, strictly positive coefficients; seamlessly integrates with the runtime contract of `medha_text_engine(text)`.

### Model 2: Core 5 MuRIL XGBoost Regressor
- **Status**: Nonlinear baseline on Core 5 features.
- **Inputs**: 5 Core MuRIL output features.
- **Hyperparameters**: `n_estimators=100`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `random_state=42`.

### Model 3: Extended 9-Feature XGBoost Regressor (Diagnostic / Ablation Artifact)
- **Status**: **Diagnostic / Ablation Artifact** to evaluate whether longitudinal context adds incremental value beyond the 5 core MuRIL outputs.
- **Inputs**: All 9 text-derived features (including baseline and trajectory deviation).

---

## 6. Comprehensive Evaluation Results

Evaluated on **held-out available text observations** (`Text_Available == 1`):

| Model | Split | $n$ | MAE | RMSE | $R^2$ | Pearson $r$ | Spearman $\rho$ | Baseline MAE | MAE Improvement |
|---|---|---|---|---|---|---|---|---|---|
| **Ridge (Core 5) — Canonical Specialist** | Train | 15,493 | 6.4001 | 8.0273 | 0.6329 | 0.7956 | 0.8040 | 10.8732 | **+41.14%** |
| | Val | 3,340 | 6.3017 | 7.8748 | 0.6374 | 0.7987 | 0.8073 | 10.7686 | **+41.48%** |
| | **Test** | **3,362** | **6.4352** | **8.0783** | **0.6365** | **0.7978** | **0.8067** | **11.0068** | **+41.53%** |
| **XGBoost (Core 5)** | Train | 15,493 | 6.2449 | 7.8335 | 0.6504 | 0.8066 | 0.8130 | 10.8732 | **+42.57%** |
| | Val | 3,340 | 6.2913 | 7.8595 | 0.6388 | 0.7995 | 0.8075 | 10.7686 | **+41.58%** |
| | **Test** | **3,362** | **6.4496** | **8.0934** | **0.6351** | **0.7970** | **0.8054** | **11.0068** | **+41.39%** |
| **XGBoost (All 9) — Diagnostic Ablation** | Train | 15,493 | 6.2058 | 7.7803 | 0.6552 | 0.8096 | 0.8154 | 10.8732 | **+42.93%** |
| | Val | 3,340 | 6.3022 | 7.8684 | 0.6380 | 0.7992 | 0.8071 | 10.7686 | **+41.48%** |
| | **Test** | **3,362** | **6.4361** | **8.0920** | **0.6353** | **0.7971** | **0.8058** | **11.0068** | **+41.52%** |

### Key Findings:
1. **High Consistency**: Ridge and XGBoost perform almost identically on held-out test data ($R^2 \approx 0.636$, MAE $\approx 6.43 - 6.44$).
2. **No apparent overfitting / stable held-out performance**: Train $R^2 = 0.6329$ vs. Test $R^2 = 0.6365$. The linear mapping generalizes stably across unseen victims.
3. **Diagnostic Ablation (Core 5 Sufficiency)**: The All-9 experiment confirms that adding the 4 extended longitudinal features does not meaningfully improve test performance ($R^2 = 0.6353$ vs $0.6365$), validating the canonical Core-5 MuRIL mapping as the optimal, parsimonious specialist model.

---

## 7. Model Coefficients & Feature Importance

### Ridge Regression Equation (Core 5 MuRIL Features)
$$\text{Predicted DDS} = 14.2037 + 12.3504 \cdot \text{Text\_Distress} + 10.1130 \cdot \text{Fear} + 10.1067 \cdot \text{Negative\_Affect} + 9.7627 \cdot \text{Urgency} + 2.9063 \cdot \text{Threat\_Context}$$

All coefficients are strictly positive, aligning with clinical domain theory:
- `Text_Distress`: Weight = **+12.3504**
- `Fear`: Weight = **+10.1130**
- `Negative_Affect`: Weight = **+10.1067**
- `Urgency`: Weight = **+9.7627**
- `Threat_Context`: Weight = **+2.9063**

### XGBoost Feature Gain Importance (Core 5)
1. `Urgency`: **0.5195**
2. `Text_Distress`: **0.2401**
3. `Fear`: **0.1431**
4. `Negative_Affect`: **0.0885**
5. `Threat_Context`: **0.0087**

---

## 8. Artifacts Inventory

All artifacts are persisted under `models/text_dds_v2/` and `outputs/dds_v2/text/` (and mirrored in `engine/`):

### Model Artifacts (`models/text_dds_v2/`)
- `v2_text_dds_ridge_core5.pkl`: Serialized Ridge regression model (**Canonical / Recommended Specialist**).
- `v2_text_dds_xgb_core5.json`: XGBoost regression model (Core 5 features baseline).
- `v2_text_dds_xgb_all9.json`: XGBoost regression model (**Diagnostic / Ablation Artifact**).
- `v2_text_dds_preprocessor.pkl`: Train-fitted imputer.
- `v2_text_dds_features.json`: Metadata defining core and extended feature subsets.
- `v2_text_dds_metrics.json`: Full evaluation results across all splits.
- `v2_text_dds_importance.csv`: Feature importances.

### Prediction Outputs (`outputs/dds_v2/text/`)
- `test_text_dds_predictions.csv`: 4,500 test rows with victim IDs, actual DDS, availability flag, and model predictions.
- `val_text_dds_predictions.csv`: 4,500 validation rows.

### Automated Test Suite
- `engine/tests/test_v2_text_dds.py`: 6 automated test suites (all passing).

---

## 9. Test Suite Verification

Executed: `pytest engine/tests`
- **Result: 23 passed in 3.28s**
  - `engine/tests/test_v2_feature_policy.py`: 11 passed
  - `engine/tests/test_v2_structured_dds.py`: 6 passed
  - `engine/tests/test_v2_text_dds.py`: 6 passed

---

## 10. Confirmation & Limitations

1. **Existing Text Engine Preserved**: MuRIL weights and `medha_text_engine.py` were not altered or retrained.
2. **Authoritative Split Preserved**: Step 3 victim-level split was maintained exactly.
3. **Synthetic Dataset**: Performance reflects the synthetic benchmark. Clinical validation requires real-world data.
4. **Modality Isolation**: Zero cross-modal leakage between Structured, Text, and Voice specialists.

**STOPPED.** Step 6 is complete and ready for review.
