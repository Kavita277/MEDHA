# MEDHA V2 — STEP 10B CORRECTION: LEAKAGE-SAFE FUSION TRAINING AND CANDIDATE SELECTION

## Executive Summary

This document formalises the methodological correction to **MEDHA V2 Step 10B**. 

In the preliminary Step 10B experiment, the fusion model demonstrated strong initial metrics (test MAE ~6.0626), but two critical methodological flaws were identified:
1. **In-Sample Stacking Leakage**: Specialist models were trained on the full 700 training victims and evaluated on those same training victims to generate the inputs for training the fusion meta-learners. This gave the fusion layer over-optimistic, in-sample training features.
2. **Test-Based Candidate Selection**: Fusion candidates were compared and selected based on **Test set** performance, invalidating the Test split as an untouched final holdout evaluation.

In this corrected Step 10B implementation:
- We implement **5-fold victim-level cross-fitting** across all 700 training victims, producing true **Out-of-Fold (OOF)** predictions for all 21,000 training rows.
- Fusion candidates are trained exclusively on OOF predictions.
- Candidate selection is conducted **strictly on the Validation set** (150 victims, 4,500 rows).
- The **Test set remains 100% UNTOUCHED** (not loaded, evaluated, tuned, or inspected during candidate selection).
- The preliminary Step 10B and Step 10C artifacts are fully preserved as an exploratory/preliminary benchmark in their original namespaces. Corrected artifacts reside in dedicated `_oof` namespaces.

---

## 1. Methodological Flaws in Preliminary Step 10B

### Problem 1: In-Sample Stacking Leakage
In stacking meta-learning, if the base specialists are trained on the same data on which their predictions are evaluated for training the second-stage meta-learner:
- The base models have already memorized or tightly fit individual training patterns.
- The meta-learner receives training inputs with artificially low residual errors and distorted variance.
- The meta-learner learns weights optimized for overfitted specialist outputs, which degrades generalization to unseen victims.

### Problem 2: Test-Based Model Selection
In the preliminary experiment, Candidates A, B, and C were evaluated on the Test set, and Candidate C was selected specifically because its Test MAE (6.0626) was superior to Candidate B (6.1089).
- Selecting a model by looking at Test metrics violates statistical holdout isolation.
- The reported Test MAE becomes an optimistic, biased estimate rather than an unbiased benchmark.

---

## 2. Corrected 5-Fold Victim-Level OOF Cross-Fitting Protocol

To eliminate in-sample leakage, we implemented a 5-fold cross-fitting protocol partitioned strictly at the **Victim_ID** level:

```
Total Training Set: 700 Victims (21,000 longitudinal observations, 30 per victim)

Fold 1: 560 Train Victims (16,800 rows) | 140 Held-Out Victims (4,200 rows)
Fold 2: 560 Train Victims (16,800 rows) | 140 Held-Out Victims (4,200 rows)
Fold 3: 560 Train Victims (16,800 rows) | 140 Held-Out Victims (4,200 rows)
Fold 4: 560 Train Victims (16,800 rows) | 140 Held-Out Victims (4,200 rows)
Fold 5: 560 Train Victims (16,800 rows) | 140 Held-Out Victims (4,200 rows)
```

### Critical Victim-Level Constraints
1. **Zero Overlap**: For every fold $k \in \{1..5\}$, the held-out victims $V_k$ and training victims $T_k$ are completely disjoint ($V_k \cap T_k = \emptyset$).
2. **Temporal Integrity**: All 30 timepoints belonging to an individual victim remain grouped in the same fold. Individual rows are never randomly split.
3. **Complete Coverage**: Every one of the 700 training victims appears as a held-out victim in exactly one fold ($\bigcup_{k=1}^5 V_k = V_{\text{train}}$, with $V_i \cap V_j = \emptyset$ for $i \neq j$).
4. **Fold Preprocessor Isolation**: For every fold, preprocessing pipelines (median imputers, ordinal encoders) are fitted **only** on that fold's 560 specialist-training victims. No global train preprocessing is shared during cross-fitting.

---

## 3. Specialist Training Per Fold

Inside each fold $k$, four independent specialists were fitted strictly on the 560 training victims:

1. **Structured DDS Specialist (XGBoost Regressor)**:
   - 42 approved structured features (clinical, context, protective, engagement baselines).
   - Numeric features: Median imputer fitted on fold training data.
   - Categorical features (`Case_Type`, `Case_Stage`, `Episode_Severity`): Constant imputer + Ordinal encoder fitted on fold training data.
   - Model: `XGBRegressor(objective='reg:squarederror', n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8, colsample_bytree=0.8, random_state=42)`.
   - Output: `Struct_Pred` for the 140 held-out victims; `Struct_Available = 1`.

2. **Text DDS Specialist (Ridge Regressor, Core-5)**:
   - 5 core MuRIL text features (`Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`).
   - Fitted strictly on fold training rows where `Text_Available == 1`.
   - Median imputer fitted on available text rows in fold training data.
   - Model: `Ridge(alpha=1.0, random_state=42)`.
   - Output: `Text_Pred` for held-out victims where `Text_Available == 1`. When `Text_Available == 0`, `Text_Pred` is masked as `NaN` (and imputed to 0.0 with `Text_Available = 0` in the learned fusion feature matrix).

3. **Voice DDS Specialist (Ridge Regressor, Core-5)**:
   - 5 core acoustic/prosodic features (`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`).
   - Fitted strictly on fold training rows where `Voice_Available == 1`.
   - Median imputer fitted on available voice rows in fold training data.
   - Model: `Ridge(alpha=1.0, random_state=42)`.
   - Output: `Voice_Pred` for held-out victims where `Voice_Available == 1`. When `Voice_Available == 0`, `Voice_Pred` is masked as `NaN` (and imputed to 0.0 with `Voice_Available = 0` in the learned fusion feature matrix).

4. **Behaviour DDS Specialist (Ridge Regressor, Extended-10)**:
   - 10 behaviour features (`Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation`, `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Baseline_Response_Delay`, `Baseline_Engagement`, `Behaviour_Trend`).
   - Absolute deviations applied: `|Engagement_Deviation|` and `|Response_Delay_Deviation|`.
   - Median imputer fitted on fold training data.
   - Model: `Ridge(alpha=1.0, random_state=42)`.
   - Output: `Behav_Pred` for held-out victims; `Behav_Available = 1`.

---

## 4. Specialist Out-of-Fold (OOF) Training Performance

The 5 held-out prediction sets were concatenated to assemble the full 21,000-row training matrix. The true out-of-fold performance of each specialist on the training victims is:

| Specialist Model | Feature Set | N (Observed) | OOF MAE | OOF RMSE | OOF R² | OOF Pearson |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Structured Specialist** (XGBoost) | 42 features | 21,000 (100.0%) | **6.2015** | **7.7884** | **0.6448** | **0.8031** |
| **Text Specialist** (Ridge Core-5) | 5 MuRIL features | 15,493 (73.8%) | **6.4034** | **8.0313** | **0.6325** | **0.7953** |
| **Voice Specialist** (Ridge Core-5) | 5 Acoustic features | 7,634 (36.4%) | **6.4969** | **8.1447** | **0.6414** | **0.8009** |
| **Behaviour Specialist** (Ridge Ext-10)| 10 Behaviour features| 21,000 (100.0%) | **7.4513** | **9.3463** | **0.4885** | **0.6989** |

*Key finding*: These OOF metrics are realistic, slightly higher than in-sample training metrics, and accurately reflect generalization to unseen victims.

---

## 5. Fusion Candidate Architectures & Training

All fusion candidates were trained **strictly on the OOF training dataset** (21,000 observations):

### Candidate A: Modality-Aware Weighted Average
- **Weight Derivation**: Weights are derived strictly from the specialist OOF training MAEs using inverse-MAE normalization ($w_i \propto 1 / \text{MAE}_i^{\text{OOF}}$):
  - Structured: $1 / 6.2015 \rightarrow$ **0.266292** (26.63%)
  - Text: $1 / 6.4034 \rightarrow$ **0.257896** (25.79%)
  - Voice: $1 / 6.4969 \rightarrow$ **0.254184** (25.42%)
  - Behaviour: $1 / 7.4513 \rightarrow$ **0.221627** (22.16%)
  - Sum of base weights: **1.000000**
- **Inference**: Dynamically renormalizes weights across available modalities for each observation. Missing modalities contribute 0 weight.

### Candidate B: Ridge Stacking Regressor
- **Features**: 8 input features (`Struct_Pred`, `Text_Pred`, `Voice_Pred`, `Behav_Pred`, `Struct_Available`, `Text_Available`, `Voice_Available`, `Behav_Available`).
- Missing predictions imputed to 0.0, paired with explicit availability flag = 0.
- Fitted with 5-fold cross-validation on OOF training data (`RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0], cv=5)`).
- Selected $\alpha = 1.0$, Intercept $= 8.5235$.
- Coefficients:
  - `Struct_Pred`: $+0.7930$
  - `Text_Pred`: $+0.2566$
  - `Voice_Pred`: $+0.1722$
  - `Behav_Pred`: $-0.0053$
  - `Text_Available`: $-10.3167$
  - `Voice_Available`: $-6.8497$
  - `Struct_Available`: $0.0000$ (constant)
  - `Behav_Available`: $0.0000$ (constant)

### Candidate C: XGBoost Stacking Regressor
- **Features**: Same 8 approved input features.
- Hyperparameters: `objective='reg:squarederror'`, `n_estimators=100`, `max_depth=3`, `learning_rate=0.1`, `subsample=0.8`, `colsample_bytree=0.8`, `min_child_weight=10`, `reg_alpha=1.0`, `reg_lambda=5.0`, `random_state=42`.
- Trained strictly on the 21,000 OOF rows.
- Feature importances:
  - `Struct_Pred`: **66.97%**
  - `Text_Pred`: **13.77%**
  - `Text_Available`: **9.04%**
  - `Behav_Pred`: **4.94%**
  - `Voice_Pred`: **3.60%**
  - `Voice_Available`: **1.68%**

---

## 6. Candidate Selection on the Validation Set

Validation predictions from canonical specialists (trained on all 700 training victims) were loaded for the 150 validation victims (4,500 rows).

Each fusion candidate was evaluated on the validation set.

### Validation Performance Comparison

| Candidate Model | Validation MAE | Validation RMSE | Validation R² | Validation Pearson | Validation Spearman |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Candidate A (Weighted Average)** | 6.0940 | 7.6155 | 0.6444 | 0.8056 | 0.8116 |
| **Candidate B (Ridge Stacking)** | 5.9062 | 7.3713 | 0.6669 | 0.8167 | 0.8209 |
| **Candidate C (XGBoost Stacking)** | **5.8851** | **7.3544** | **0.6684** | **0.8176** | **0.8209** |

### Selection Decision
- **Winning Candidate**: **Candidate C (XGBoost Stacking)**
- **Selection Basis**: Lowest Validation MAE (**5.8851** vs 5.9062 for Ridge and 6.0940 for Weighted Average).
- **Validation Gain**: Candidate C achieves a **+0.2089 MAE improvement** over Candidate A and **+0.0211 MAE improvement** over Candidate B on unseen validation victims.
- **Confirmation**: **The Test set was NOT evaluated, inspected, or used in this decision.**

---

## 7. Model Freezing and Artifact Index

The selected model (**Candidate C: XGBoost**) is frozen with its exact hyperparameters, feature ordering, and availability handling.

All corrected artifacts are preserved in the `fusion_oof` namespace:

### Output Artifacts (`engine/outputs/dds_v2/fusion_oof/` and `outputs/dds_v2/fusion_oof/`)
- `fusion_oof_fold_assignments.csv`: 700 training victims with their fold IDs (1..5, exactly 140 per fold).
- `fusion_oof_train_predictions.csv`: 21,000 training observations with OOF predictions and availability flags.
- `fusion_validation_predictions.csv`: 4,500 validation observations with canonical specialist predictions and fused predictions.
- `fusion_candidate_metrics.csv`: Comparative validation metrics for Candidates A, B, and C.
- `fusion_oof_training_report.json`: High-level summary of the training run.

### Model Artifacts (`engine/models/v2/fusion_oof/` and `models/v2/fusion_oof/`)
- `fusion_model.json`: Frozen XGBoost fusion model artifact.
- `fusion_selected_model.json`: Selection rationale, metric, and training protocol metadata.
- `fusion_feature_config.json`: Canonical feature ordering and approved/forbidden lists.
- `fusion_preprocessor.json` / `fusion_preprocessor.pkl`: Imputation and availability flag handling schema.
- `v2_fusion_oof_weights.json`: Candidate A inverse-OOF-MAE weights.
- `v2_fusion_oof_ridge.pkl`: Trained Candidate B Ridge model.
- `v2_fusion_oof_xgb.json`: Trained Candidate C XGBoost model.
- `fusion_oof_metadata.json`: Complete audit trail including OOF specialist metrics and coefficients.

---

## 8. Preserved Historical Benchmarks

The preliminary Step 10B and 10C artifacts remain untouched for historical reference:
- `engine/models/v2/fusion/` (preliminary fusion models)
- `engine/outputs/dds_v2/fusion/` (preliminary fusion predictions)
- `walkthrough_step10c.md` (preliminary Step 10C evaluation walkthrough)

The preliminary test MAE of ~6.0626 is strictly documented as an exploratory/preliminary benchmark, **not** the final unbiased MEDHA V2 Fusion result.

---

## 9. Verification & Unit Tests

A comprehensive test suite was executed:
```powershell
python -m pytest engine/tests/test_v2_fusion_oof.py -v
python -m pytest engine/tests/ -v
```

### Test Suite Results
- `test_v2_fusion_oof.py`: **9/9 passed**
- Total test suite (`engine/tests/`): **93/93 passed** (100% pass rate)

Tested conditions verified:
- [x] Train/validation/test victim overlap = 0.
- [x] Fold victim overlap = 0.
- [x] Exactly 140 victims per fold; exactly 21,000 OOF rows.
- [x] No duplicate `(Victim_ID, Timepoint)` keys.
- [x] Zero in-sample specialist predictions used for fusion training.
- [x] Strict feature policy: Zero forbidden features (`Actual_DDS`, `Future_Escalation_Label`, `Previous_DDS`, `Rolling_DDS_Mean`, etc.).
- [x] Candidate selection strictly on Validation MAE; Test set untouched.
- [x] Candidate A weights derived strictly from OOF training MAEs.
- [x] Missing modality handling and availability flags verified.
- [x] Deterministic inference verified.
