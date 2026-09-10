# MEDHA V2 Model Cards

The MEDHA V2 system comprises a pipeline of independent models that are stacked or executed in parallel. All components are fully deterministic and frozen.

## 1. System Inventory

| Component | Algorithm | Inputs | Output | Artifact | Frozen |
| --------- | --------- | ------ | ------ | -------- | ------ |
| **Structured DDS** | XGBoost Regressor | 42 | DDS (0-100) | `engine/models/structured_dds_v2/v2_structured_dds_xgb.json` | YES |
| **Text DDS** | Ridge Regressor | 5 | DDS (0-100) | `engine/models/text_dds_v2/v2_text_dds_ridge_core5.pkl` | YES |
| **Voice DDS** | Ridge Regressor | 5 | DDS (0-100) | `engine/models/voice_dds_v2/v2_voice_dds_ridge_core5.pkl` | YES |
| **Behaviour DDS** | Ridge Regressor | 10 | DDS (0-100) | `engine/models/behaviour_dds_v2/v2_behaviour_dds_ridge_all10.pkl` | YES |
| **Fusion** | XGBoost Regressor | 8 | DDS (0-100) | `engine/models/v2/fusion_final/fusion_model.json` | YES |
| **GRU** | PyTorch GRU | (7, 57) | Prob. (0-1) | `engine/models/v2/gru/best_gru_model.pth` | YES |
| **Triage** | Ruleset | 3 | Triage Category | N/A (Code Logic) | YES |

---

## 2. Structured DDS

* **Algorithm**: XGBoost Regressor
* **Objective**: `reg:squarederror`
* **Features**: 42 (`engine/models/v2/v2_structured_dds_features.json`)
* **Preprocessor**: `engine/models/structured_dds_v2/v2_structured_dds_preprocessor.pkl`
* **Artifact**: `engine/models/structured_dds_v2/v2_structured_dds_xgb.json`
* **Hyperparameters**:
  * `n_estimators`: 100
  * `max_depth`: 6
  * `learning_rate`: 0.1

---

## 3. Text DDS

* **Algorithm**: Ridge Regression (Core-5)
* **Features**: 5 (`engine/models/text_dds_v2/v2_text_dds_features.json`)
* **Preprocessor**: `engine/models/text_dds_v2/v2_text_dds_preprocessor.pkl`
* **Artifact**: `engine/models/text_dds_v2/v2_text_dds_ridge_core5.pkl`
* **Hyperparameters**:
  * `alpha`: 1.0

---

## 4. Voice DDS

* **Algorithm**: Ridge Regression (Core-5)
* **Features**: 5 (`engine/models/voice_dds_v2/v2_voice_dds_features.json`)
* **Preprocessor**: `engine/models/voice_dds_v2/v2_voice_dds_preprocessor.pkl`
* **Artifact**: `engine/models/voice_dds_v2/v2_voice_dds_ridge_core5.pkl`
* **Hyperparameters**:
  * `alpha`: 1.0

---

## 5. Behaviour DDS

* **Algorithm**: Ridge Regression (Ext-10)
* **Features**: 10 (`engine/models/behaviour_dds_v2/v2_behaviour_dds_features.json`)
* **Preprocessor**: `engine/models/behaviour_dds_v2/v2_behaviour_dds_preprocessor.pkl`
* **Artifact**: `engine/models/behaviour_dds_v2/v2_behaviour_dds_ridge_all10.pkl`
* **Hyperparameters**:
  * `alpha`: 1.0

---

## 6. Fusion Engine (Candidate C)

* **Algorithm**: XGBoost Regressor
* **Features**: 8 (`engine/models/v2/fusion_final/fusion_feature_config.json`)
  * `Struct_Pred`, `Text_Pred`, `Voice_Pred`, `Behav_Pred`, `Struct_Available`, `Text_Available`, `Voice_Available`, `Behav_Available`
* **Artifact**: `engine/models/v2/fusion_final/fusion_model.json`
* **Hyperparameters**:
  * `n_estimators`: 100
  * `max_depth`: 3
  * `learning_rate`: 0.1
  * `subsample`: 0.8
  * `colsample_bytree`: 0.8
  * `reg_alpha`: 1.0
  * `reg_lambda`: 5.0
  * `random_state`: 42

---

## 7. GRU Temporal Risk

* **Algorithm**: PyTorch GRU
* **Features**: 57 whitelisted (`engine/models/v2/gru_sequences/feature_config.json`)
* **Sequence**: 7 historical timesteps
* **Preprocessor**: `engine/models/v2/gru_sequences/scaler.joblib`
* **Artifact**: `engine/models/v2/gru/best_gru_model.pth`
* **Threshold**: `engine/models/v2/gru/threshold_config.json` (0.75)
* **Parameters**: 23,681 trainable parameters
* **Hyperparameters**:
  * `hidden_size`: 64
  * `num_layers`: 1
  * `dropout`: 0.3
  * `optimizer`: Adam
  * `learning_rate`: 0.001
  * `weight_decay`: 0.0001
  * `loss`: BCEWithLogitsLoss
  * `batch_size`: 128
  * `best_epoch`: 4
  * `patience`: 7
