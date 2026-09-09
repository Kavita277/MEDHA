# Walkthrough — MEDHA V2 Step 10B Correction

## Leakage-Safe Fusion Training and Validation Candidate Selection

This walkthrough documents the execution and verification of the **MEDHA V2 Step 10B Correction**, which eliminates meta-level stacking leakage and test-based candidate selection.

---

## 1. Problem Statement & Objectives

In the preliminary Step 10B experiment:
1. Specialists were trained on all 700 train victims, and their in-sample predictions were fed into the fusion model, introducing stacking leakage.
2. The winning candidate was chosen based on Test set MAE, compromising the Test set as an unbiased holdout.

**Corrections Implemented**:
- **5-fold victim-level cross-fitting** on 700 train victims to generate out-of-fold (OOF) predictions for all 21,000 training rows.
- Preprocessing and specialists trained strictly on 4/5 training victims (560 victims) per fold.
- Candidate models (Weighted Average, Ridge, XGBoost) trained strictly on OOF predictions.
- Candidate selection performed strictly on the **Validation set** (150 victims, 4,500 rows).
- **Test set remained completely untouched.**
- Preliminary Step 10B/10C artifacts preserved in `engine/models/v2/fusion/` and `engine/outputs/dds_v2/fusion/`.

---

## 2. Key Results

### A. Specialist Out-of-Fold (OOF) Performance on Train Set (21,000 Rows)

| Specialist | Features | N Observed | OOF MAE | OOF RMSE | OOF R² | OOF Pearson |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Structured** (XGBoost) | 42 structured features | 21,000 (100%) | **6.2015** | 7.7884 | 0.6448 | 0.8031 |
| **Text** (Ridge Core-5) | 5 MuRIL features | 15,493 (73.8%) | **6.4034** | 8.0313 | 0.6325 | 0.7953 |
| **Voice** (Ridge Core-5) | 5 Acoustic features | 7,634 (36.4%) | **6.4969** | 8.1447 | 0.6414 | 0.8009 |
| **Behaviour** (Ridge Ext-10) | 10 Behaviour features | 21,000 (100%) | **7.4513** | 9.3463 | 0.4885 | 0.6989 |

### B. Fusion Candidate Validation Performance (150 Victims, 4,500 Rows)

| Candidate | Val MAE | Val RMSE | Val R² | Val Pearson | Val Spearman |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Candidate A (Weighted Average)** | 6.0940 | 7.6155 | 0.6444 | 0.8056 | 0.8116 |
| **Candidate B (Ridge Stacking)** | 5.9062 | 7.3713 | 0.6669 | 0.8167 | 0.8209 |
| **Candidate C (XGBoost Stacking)** | **5.8851** | **7.3544** | **0.6684** | **0.8176** | **0.8209** |

**Selection Decision**:
- **Candidate C (XGBoost Stacking)** selected based on lowest Validation MAE (**5.8851**).
- Test set was **not evaluated or used** in candidate selection.

---

## 3. Artifact Verification

All corrected artifacts were created in dedicated `_oof` directories without overwriting preliminary experiments:

- **Outputs**: `engine/outputs/dds_v2/fusion_oof/` (and root `outputs/dds_v2/fusion_oof/`):
  - `fusion_oof_fold_assignments.csv` (700 rows, 140 per fold)
  - `fusion_oof_train_predictions.csv` (21,000 rows)
  - `fusion_validation_predictions.csv` (4,500 rows)
  - `fusion_candidate_metrics.csv`
  - `fusion_oof_training_report.json`
- **Models**: `engine/models/v2/fusion_oof/` (and root `models/v2/fusion_oof/`):
  - `fusion_model.json` (frozen Candidate C XGBoost model)
  - `fusion_selected_model.json`
  - `fusion_feature_config.json`
  - `fusion_preprocessor.json` & `fusion_preprocessor.pkl`
  - `v2_fusion_oof_weights.json` (Candidate A weights)
  - `v2_fusion_oof_ridge.pkl` (Candidate B Ridge model)
  - `v2_fusion_oof_xgb.json` (Candidate C XGBoost model)
  - `fusion_oof_metadata.json`

---

## 4. Test Suite Execution

All unit tests and regression checks passed cleanly:
```powershell
python -m pytest engine/tests/
```
**Result**: **93/93 passed** (100% pass rate).
- `test_v2_fusion_oof.py`: 9 passed
- `test_v2_fusion.py`: 47 passed
- `test_v2_feature_policy.py`: 11 passed
- `test_v2_structured_dds.py`: 6 passed
- `test_v2_text_dds.py`: 6 passed
- `test_v2_voice_dds.py`: 7 passed
- `test_v2_behaviour_dds.py`: 7 passed
