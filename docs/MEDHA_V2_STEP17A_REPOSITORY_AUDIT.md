# MEDHA V2 Step 17A: Comprehensive Repository Audit

## 1. Executive Summary

This document represents the final pre-handoff audit of the MEDHA V2 system. All model development, tuning, and evaluation stages are **frozen**. This audit catalogs the exact repository state, traces the end-to-end data pipeline to ensure complete backend readiness, and maps all final metrics. 

**Critical Warning**: No models, data splits, or feature ordering may be altered after this point.

## 2. Repository Map

* **`engine/v2/`**: Contains the canonical V2 pipeline (`medha_v2_pipeline.py`) and training scripts for all V2 components. **(KEEP - REQUIRED FOR BACKEND)**
* **`engine/models/`**: Contains the canonical serialized model artifacts (XGBoost, Ridge, GRU), preprocessors, feature configurations, and metadata JSON files. **(KEEP - MODEL ARTIFACT)**
* **`engine/fusion_engine/`**: Experimental scripts and intermediate diagnostics used during Step 10 & 11 Fusion development. **(ARCHIVE / KEEP - HISTORICAL REFERENCE)**
* **`engine/gru-temporal-risk/` & `engine/legacy_v1/`**: V1 models and inference APIs. **(KEEP - ARCHIVE / HISTORICAL REFERENCE)**
  * *Reason*: The V1 implementation is useful for documenting the migration from the old leaky 72-feature GRU to the leakage-safe V2 architecture. Do not delete V1. Keep it isolated from V2 runtime code.
* **`engine/outputs/` & `outputs/`**: Canonical test metrics, OOF predictions, and diagnostic test sets. **(KEEP - REFERENCE)**
* **`docs/`**: Official architectural decision records (ADRs), audits, and ablation studies. **(KEEP - REFERENCE)**
* **`scratch/`**: Temporary investigative scripts. **(SAFE TO DELETE)**
* **`engine/tests/`**: Unit and integration tests for V2 components. **(KEEP - TRAINING / REPRODUCIBILITY)**

## 3. V2 Pipeline Map

The executable code tracing the data flow from raw input to Priority triage:

**1. Structured Preprocessing & Specialist**
* **Function**: `MedhaV2Pipeline.predict_v2` -> `self.struct_preproc.transform` -> `self.struct_model.predict`
* **Input**: 42 raw tabular features
* **Preprocessing**: `ZeroImputerWithAvailabilityFlag` mapping to 42 variables. Missing continuous = median. Missing categorical = custom encoding. 
* **Output**: `Struct_Pred` (0-100), `Struct_Available = 1.0`

**2. Text Preprocessing & Specialist**
* **Function**: `MedhaV2Pipeline.predict_v2` -> `self.text_preproc.transform` -> `self.text_model.predict`
* **Input**: 5 MuRIL core NLP features (`Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`)
* **Preprocessing**: Imputer.
* **Output**: `Text_Pred` (0-100) or `NaN`, `Text_Available = 1.0 / 0.0`

**3. Voice Preprocessing & Specialist**
* **Function**: `MedhaV2Pipeline.predict_v2` -> `self.voice_preproc.transform` -> `self.voice_model.predict`
* **Input**: 5 Acoustic features (`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`)
* **Preprocessing**: Imputer.
* **Output**: `Voice_Pred` (0-100) or `NaN`, `Voice_Available = 1.0 / 0.0`

**4. Behaviour Preprocessing & Specialist**
* **Function**: `MedhaV2Pipeline.predict_v2` -> `self.behav_preproc.transform` -> `self.behav_model.predict`
* **Input**: 10 Extended Behaviour features (e.g., `App_Interaction_Duration`, absolute deviations).
* **Preprocessing**: Absolute value extraction on `Engagement_Deviation` and `Response_Delay_Deviation`. Imputer.
* **Output**: `Behav_Pred` (0-100), `Behav_Available = 1.0`

**5. Fusion Feature Construction & XGBoost**
* **Function**: `MedhaV2Pipeline.predict_v2`
* **Input**: 8 meta-features mapped from Specialist predictions and availabilities.
* **Handling**: Missing modalities replaced by `0.0`.
* **Output**: `Fusion_DDS_Prediction` (clamped to 0.0 - 100.0)

**6. GRU Historical Construction & Future Risk**
* **Function**: `MedhaV2Pipeline.predict_v2` -> `gru_model.predict_proba()`
* **Input**: 57 explicit whitelisted numeric features per observation. Pre-filled NaN/infs to 0.0 before sequence construction.
* **Sequence**: Grouped by `Victim_ID`, ordered by `Timepoint`. `window = features[i-7 : i]` (strictly past history). Scaled by `gru_scaler`.
* **Output**: `Temporal_Risk_Score` (0.0-1.0), `Future_Escalation_Flag` (1 if score >= 0.75, else 0).

**7. Priority/Triage**
* **Function**: `engine/v2/priority_triage.py` (Engineering Demonstration)
* **Input**: `Fusion_DDS_Prediction`, `Temporal_Risk_Score`, `Future_Escalation_Flag`
* **Output**: High / Medium / Low priority categorizations. *(Note: Not integrated directly into the core pipeline return object).*

## 4. Model Inventory & Exact Paths

| Component | Model Type | Exact Repository Path | Input Dimension | Output | Frozen? |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **Structured DDS** | XGBoost Regressor | `engine/models/structured_dds_v2/v2_structured_dds_xgb.json` | 42 | DDS (0-100) | YES |
| **Text DDS** | Ridge Regressor | `engine/models/text_dds_v2/v2_text_dds_ridge_core5.pkl` | 5 | DDS (0-100) | YES |
| **Voice DDS** | Ridge Regressor | `engine/models/voice_dds_v2/v2_voice_dds_ridge_core5.pkl` | 5 | DDS (0-100) | YES |
| **Behaviour DDS** | Ridge Regressor | `engine/models/behaviour_dds_v2/v2_behaviour_dds_ridge_all10.pkl` | 10 | DDS (0-100) | YES |
| **Fusion (Cand. C)** | XGBoost Regressor | `engine/models/v2/fusion_final/fusion_model.json` | 8 | DDS (0-100) | YES |
| **GRU** | PyTorch GRU | `engine/models/v2/gru/best_gru_model.pth` | (7, 57) | Prob. (0-1) | YES |

**Canonical Auxiliary Artifacts loaded by `MedhaV2Pipeline`:**
- Structured Config: `engine/models/v2/v2_structured_dds_features.json`
- Structured Preprocessor: `engine/models/structured_dds_v2/v2_structured_dds_preprocessor.pkl`
- Text Config: `engine/models/text_dds_v2/v2_text_dds_features.json`
- Text Preprocessor: `engine/models/text_dds_v2/v2_text_dds_preprocessor.pkl`
- Voice Config: `engine/models/voice_dds_v2/v2_voice_dds_features.json`
- Voice Preprocessor: `engine/models/voice_dds_v2/v2_voice_dds_preprocessor.pkl`
- Behaviour Config: `engine/models/behaviour_dds_v2/v2_behaviour_dds_features.json`
- Behaviour Preprocessor: `engine/models/behaviour_dds_v2/v2_behaviour_dds_preprocessor.pkl`
- Fusion Config: `engine/models/v2/fusion_final/fusion_feature_config.json`
- GRU Feature Config: `engine/models/v2/gru_sequences/feature_config.json`
- GRU Threshold Config: `engine/models/v2/gru/threshold_config.json`
- GRU Scaler: `engine/models/v2/gru_sequences/scaler.joblib`

## 5. Feature Contracts

**Fusion Model Contract:**
- **Exact Input Dimension**: 8
- **Exact Feature Order**: 
  1. `Struct_Pred`
  2. `Text_Pred`
  3. `Voice_Pred`
  4. `Behav_Pred`
  5. `Struct_Available`
  6. `Text_Available`
  7. `Voice_Available`
  8. `Behav_Available`
- **Missing Modality Semantics**: Missing modality prediction set to `0.0`. Availability flag set to `0.0`.

**GRU Model Contract:**
- **Exact Input Dimension**: 57 whitelisted numerical features. 
- **Sequence Length**: 7 (strictly trailing timesteps: `[i-7 : i]`).
- **Temporal Alignment**: Current timestep `i` features are EXCLUDED from the window predicting `i`'s future risk (strict target leakage guard). 
- **Scaler Behavior**: `StandardScaler` fitted exclusively on Train data; applied per 7x57 matrix. 
- **Target**: `Future_Escalation_Label`
- **Threshold**: `0.75`

## 6. Model Parameters

- **Structured DDS**: XGBoost Regressor. `n_estimators=100`, `max_depth=6`, `learning_rate=0.1`, `objective="reg:squarederror"`. 42 features.
- **Text DDS**: Ridge Regression, `alpha=1.0` (Core-5). 5 features.
- **Voice DDS**: Ridge Regression, `alpha=1.0` (Core-5). 5 features.
- **Behaviour DDS**: Ridge Regression, `alpha=1.0` (Ext-10). 10 features. Absolute deviations enforced.
- **Fusion (Candidate C)**: XGBoost Regressor, 8 features. 100 trees (`n_estimators`), `max_depth=3`, `learning_rate=0.1`. `subsample=0.8`, `colsample_bytree=0.8`, `reg_alpha=1.0`, `reg_lambda=5.0`. 
- **GRU**: PyTorch GRU. `input_size=57`, `hidden_size=64`, `num_layers=1`, `dropout=0.3`. Output FC=64->1. `optimizer=Adam(lr=0.001, weight_decay=0.0001)`. Loss=BCEWithLogitsLoss.
  - **Best validation epoch**: 4
  - **Early stopping patience**: 7
  - **Training terminated at epoch**: 11
  - **Best checkpoint from epoch 4 was restored**.

## 7. Test Metrics Located

Metrics strictly from canonical untouched Test split evaluations:

**A. Fusion DDS Prediction (Test Set: N=4,500)**
* **MAE**: `5.9537`
* **RMSE**: `7.4925`
* **R²**: `0.6750`
* **Pearson**: `0.8217`
* **Spearman**: `0.8272`

**B. GRU Temporal Risk (Test Set: N=2,400, Threshold=0.75)**
* **Accuracy**: `0.8358`
* **Precision**: `0.2981`
* **Recall**: `0.4297`
* **F1**: `0.3520`
* **ROC-AUC**: `0.7953` *(threshold-independent)*
* **PR-AUC**: `0.3133` *(threshold-independent)*
* **Test Confusion Matrix**:
  - TN = 1899
  - FP = 252
  - FN = 142
  - TP = 107
* **Positive Prevalence**: 249 / 2400 = 10.375% (approx 10.38%).
* **PR-AUC Ratio**: PR-AUC is approximately 3.02 times the positive prevalence.
* *Note: Classification metrics (Accuracy, Precision, Recall, F1) are measured explicitly at the frozen threshold of 0.75.*

**C. Specialists (Evaluated via Fusion Audit, Test N=4,500)**
* **Structured**: MAE=`6.1611`, RMSE=`7.7353`, R²=`0.6536`, Pearson=`0.8086`, Spearman=`0.8146`
* **Text (Avail only, N=3,362)**: MAE=`6.4352`, RMSE=`8.0783`, R²=`0.6365`, Pearson=`0.7978`, Spearman=`0.8067`
* **Voice (Avail only, N=1,692)**: MAE=`6.3070`, RMSE=`7.9104`, R²=`0.6529`, Pearson=`0.8082`, Spearman=`0.8179`
* **Behaviour**: MAE=`7.3530`, RMSE=`9.1945`, R²=`0.5106`, Pearson=`0.7147`, Spearman=`0.7332`

## 8. Fusion Dependency / Ablation

Based on `outputs/fusion_v2/ablation_metadata.json` (Validation Split, N=4,500) and `fusion_model.json` intrinsic XGBoost importance (gain):

**A. Model Feature Importance (Intrinsic XGBoost Gain)**
* `Struct_Pred` accounts for approximately 66.97% of the model's intrinsic XGBoost gain-based feature importance.
* `Text_Pred`: ~13.77%
* `Voice_Pred`: ~3.60%
* `Behav_Pred`: ~4.94%
* `Text_Available`: ~9.04%
* `Voice_Available`: ~1.68%

**B. Incremental Ablation Impact (Validation MAE)**
* **Full Fusion (8 features)**: MAE = `5.8851`
* **No Structured**: removing Structured increases Validation MAE by `7.95%`
* **No Text**: removing Text increases Validation MAE by `2.00%`
* **No Voice**: removing Voice increases Validation MAE by `0.71%`
* **No Behaviour**: removing Behaviour changes Validation MAE by `-0.04%`

*Explicit Disclaimer: Ablation measures incremental predictive contribution in this experiment; it is not causal importance.*

## 9. Historical vs Canonical Results

* **CANONICAL: Fusion Test MAE = 5.9537**
  This is the frozen final Candidate C result selected using validation after proper OOF training, evaluated entirely blindly on the authoritative 150-victim Test set.
* **PRELIMINARY: Fusion Test MAE = 6.0626**
  This belongs to an earlier diagnostic/preliminary evaluation (from Step 10A Fusion Audit or early testing before the OOF stacking architecture was strictly locked). It is not the frozen model's performance.

## 10. Test and Reproducibility Status

* **Status**: DETERMINISTIC.
* **Split Integrity**: 700 Train / 150 Validation / 150 Test exact victim segregation maintained.
* **Missing Modality Tests**: Proven capability to inference safely with text/voice missing, collapsing safely back to Structured.
* **Deterministic Inference**: Random seeds locked (`42`), pipelines tested. 
* **Target Leakage Guard**: All derived leakages (e.g., `Rolling_DDS_Mean`, current observation for future risk) stripped. 

## 11. Backend Readiness & Code Contracts

The backend developer will exclusively use the `MedhaV2Pipeline` located in `engine/v2/medha_v2_pipeline.py`.

### A. Backend Input Contract
The method `MedhaV2Pipeline.predict_v2(df)` expects a longitudinal pandas DataFrame.

| Column Category | Specific Required Columns | Datatype | Required? | Missing Behavior (NaN allowed?) | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Identity/Temporal** | `Victim_ID`, `Timepoint` | String, Int | **YES** | NO | GRU Grouping |
| **Structured Features** | 42 columns matching `v2_structured_dds_features.json` | Numeric | **YES** | YES (Imputed) | Structured, GRU |
| **Text Features** | 5 MuRIL core columns | Numeric | **YES** | YES (Imputed) | Text, GRU |
| **Voice Features** | 5 Acoustic columns | Numeric | **YES** | YES (Imputed) | Voice, GRU |
| **Behaviour Features** | 10 Behaviour columns | Numeric | **YES** | YES (Imputed/Deviations) | Behaviour, GRU |
| **GRU Specific** | Any additional columns mapped in `feature_whitelist` | Numeric | **YES** | YES (Imputed to 0.0) | GRU |
| **Availability Flags** | `Text_Available`, `Voice_Available` | Numeric/Binary | **NO** | Derived dynamically by code via `.get(..., 0)` | Text, Voice, Fusion |

*(Note: `Struct_Available` and `Behav_Available` are unconditional; the pipeline forces them to 1.0).*

### B. Backend Output Contract
The method `MedhaV2Pipeline.predict_v2(df)` explicitly appends and returns the following columns:

| Output Column | Datatype | Range / Values | Description |
| :--- | :--- | :--- | :--- |
| `Struct_Pred` | Float | 0.0 - 100.0 | Structured prediction |
| `Struct_Available` | Float | 1.0 | Unconditional availability flag |
| `Text_Pred` | Float | 0.0 - 100.0 (or NaN) | Text prediction (NaN if unavailable) |
| `Text_Available` | Float | 0.0 or 1.0 | Derived text availability flag |
| `Voice_Pred` | Float | 0.0 - 100.0 (or NaN) | Voice prediction (NaN if unavailable) |
| `Voice_Available` | Float | 0.0 or 1.0 | Derived voice availability flag |
| `Behav_Pred` | Float | 0.0 - 100.0 | Behaviour prediction |
| `Behav_Available` | Float | 1.0 | Unconditional availability flag |
| **`Fusion_DDS_Prediction`** | Float | 0.0 - 100.0 | Final **Current DDS** score |
| **`Temporal_Risk_Score`** | Float | 0.0 - 1.0 (or NaN) | Final **Future Risk** probability |
| `Temporal_Available` | Int | 0 or 1 | 1 if enough sequence history exists (7 timesteps) |
| `Future_Escalation_Flag` | Int | 0 or 1 (or NaN) | Thresholded risk categorization (>= 0.75) |

*(Note: Priority/Triage categorization is NOT returned by `predict_v2()`. It exists separately in `engine/v2/priority_triage.py` for demonstration).*

## 12. Cleanup Classification

* **`engine/v2/medha_v2_pipeline.py`**: **KEEP** — REQUIRED FOR BACKEND
* **`engine/models/`**: **KEEP** — MODEL ARTIFACT
* **`engine/v2/train_v2_*.py`**: **KEEP** — TRAINING / REPRODUCIBILITY
* **`engine/outputs/`, `outputs/`**: **KEEP** — HISTORICAL REFERENCE
* **`docs/MEDHA_V2_STEP*.md`**: **KEEP** — HISTORICAL REFERENCE
* **`engine/gru-temporal-risk/`, `engine/legacy_v1/`**: **KEEP** — ARCHIVE / HISTORICAL REFERENCE
* **`engine/fusion_engine/`**: **KEEP** — ARCHIVE / HISTORICAL REFERENCE
* **`scratch/` scripts**: **SAFE TO DELETE**

## 13. Open Questions / Missing Evidence

* **Resolved ML questions**: The ML architecture, features, hyperparameter tuning, model artifacts, and test metric benchmarks are fully resolved and permanently frozen.
* **Remaining work**: Final repository cleanup execution and backend packaging documentation verification.

## 14. Step 17A Audit Status

* ML architecture: VERIFIED
* Frozen artifacts: VERIFIED
* Feature contracts: VERIFIED
* Test metrics: VERIFIED
* Backend input contract: VERIFIED
* Backend output contract: VERIFIED
* Repository cleanup classification: VERIFIED
* V1 deletion: NOT PERMITTED
* Model files modified: NO
* Models retrained: NO
