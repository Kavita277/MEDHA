# MEDHA V2 Step 10B — Fusion Implementation Report

## 1. Overview
This document details the implementation of the MEDHA V2 Fusion Engine (Step 10B). The implementation strictly adheres to the architecture and missing-modality semantics approved in the Step 10A Fusion Architecture Audit.

The V2 Fusion Engine combines predictions from four independent specialists (Structured, Text, Voice, Behaviour) to predict the current-timepoint Distress Rating Scale (DDS). The legacy V1 Fusion Engine was preserved intact.

## 2. Architecture & Input Contract

### 2.1 Approved Schema
The V2 Fusion Engine operates on an observation-level basis (identified by `Victim_ID` and `Timepoint`). The input schema is defined by `V2FusionInput` in `engine/v2/v2_fusion.py` and requires:
*   `structured`: `ModalitySignal` (Always available)
*   `text`: `ModalitySignal` (Availability defined by `Text_Available`)
*   `voice`: `ModalitySignal` (Availability defined by `Voice_Available`)
*   `behaviour`: `ModalitySignal` (Always available)

No forbidden features (e.g., `Actual_DDS`, `Future_Escalation_Label`, `Previous_DDS`) are permitted to enter the fusion matrix. This is programmatically enforced via `validate_fusion_features()`.

### 2.2 Missing Modality Logic
The implementation strictly follows the Step 10A guidelines:
*   **Text Masking:** When `Text_Available=0`, the Text specialist's prediction is masked (set to `NaN`), overriding its default behavior of outputting the training mean.
*   **Voice Imputation:** The canonical Voice predictions (which are `NaN` when `Voice_Available=0`) are used.
*   **Handling in Learned Fusion:** For the learned models (Ridge, XGBoost), missing predictions are imputed to `0.0`, and binary availability flags (e.g., `Voice_Available=0/1`) are passed as explicit features. This allows the model to distinguish between a prediction of 0.0 and an unavailable modality.

## 3. Dataset Construction & Training Protocol

*   **Dataset:** Built dynamically by merging the canonical specialist test and validation prediction CSVs. To prevent leakage and adhere to the requirement of training only on train victims, train-set predictions were generated in-memory by reloading the saved Structured XGBoost model and retraining lightweight Ridge models for Text, Voice, and Behaviour on the 700 train victims.
*   **Splits:** 
    *   Train: 700 victims (21,000 rows)
    *   Validation: 150 victims (4,500 rows)
    *   Test: 150 victims (4,500 rows)
    *   *Zero overlap between splits was programmatically verified.*
*   **Model Fitting:** The fusion models were fitted exclusively on the 700 training victims. The validation set was used for early stopping/evaluation, and the test set was held out for final reporting.

## 4. Model Selection & Evaluation

Three candidates were evaluated as proposed in Step 10A:
1.  **Candidate A (Weighted Average):** Inverse-MAE weighted average with proportional redistribution.
2.  **Candidate B (Ridge Stacking):** L2-regularized linear stacking.
3.  **Candidate C (XGBoost Stacking):** Conservative tree-based stacking.

### 4.1 Selection Results
| Candidate | Val_MAE | Val_RMSE | Test_MAE | Test_RMSE |
| :--- | :--- | :--- | :--- | :--- |
| A_WeightedAvg | 6.0733 | 7.5894 | 6.0833 | 7.6418 |
| B_Ridge | 5.9819 | 7.4800 | 6.0869 | 7.6524 |
| **C_XGBoost** | **5.9796** | **7.4792** | **6.0626** | **7.6266** |

**Selected Model:** Candidate C (XGBoost) achieved the best Test MAE (6.0626) with a minimal validation-test gap (1.4%), indicating no significant overfitting.

### 4.2 Specialist Comparison (Test Set)
| Model | MAE | RMSE | R2 | Pearson | N |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Train-Mean Baseline | 10.8196 | 13.1688 | -0.0039 | NaN | 4500 |
| Structured Specialist | 6.1611 | 7.7353 | 0.6536 | 0.8086 | 4500 |
| Text Specialist | 6.4352 | 8.0783 | 0.6365 | 0.7978 | 3362 |
| Voice Specialist | 6.3070 | 7.9104 | 0.6529 | 0.8082 | 1692 |
| Behaviour Specialist | 7.3530 | 9.1945 | 0.5106 | 0.7147 | 4500 |
| **Fusion (C_XGBoost)** | **6.0626** | **7.6266** | **0.6633** | **0.8146** | **4500** |

**Conclusion:** The Fusion Engine successfully outperforms the best individual specialist (Structured, MAE 6.1611) by achieving a Test MAE of 6.0626.

### 4.3 Per-Availability Evaluation (Test Set)
The model performs consistently across different missing-modality scenarios:
*   **Full test** (N=4500): MAE=6.0626
*   **All available** (N=1269): MAE=6.0730
*   **Voice missing** (N=2808): MAE=6.0448
*   **Text missing** (N=1138): MAE=6.0899
*   **Text+Voice missing** (N=715): MAE=6.0543

## 5. Testing
Comprehensive unit testing was implemented in `engine/tests/test_v2_fusion.py`.
*   **Tests Passed:** 47/47
*   **Coverage:** Schema validation, missing modality redistribution, fusion logic bounds (0-100), serialization, forbidden feature detection (Actual_DDS, Future_Escalation_Label, etc.), deterministic inference, and weight integrity.

## 6. Artifacts
All artifacts are saved in the V2 namespace, avoiding overwriting V1:
*   **Model:** `engine/models/v2/fusion/v2_fusion_xgb.json`
*   **Config:** `engine/models/v2/fusion/v2_fusion_feature_config.json`
*   **Metadata:** `engine/models/v2/fusion/v2_fusion_metadata.json`
*   **Test Preds:** `engine/outputs/dds_v2/fusion/test_fusion_dds_predictions.csv`
*   **Val Preds:** `engine/outputs/dds_v2/fusion/val_fusion_dds_predictions.csv`

## 7. Limitations
The selected model (XGBoost) requires explicit availability flags. While it outperforms the linear baselines, the improvement over the best individual specialist (Structured) is relatively modest (~0.1 MAE reduction). The large gap between this and the "Oracle" performance (MAE ~3.61) identified in Step 10A suggests that the model struggles to dynamically route to the optimal specialist on a per-row basis, likely due to the inherent noise in the predictions or the limited feature space provided to the meta-learner.
