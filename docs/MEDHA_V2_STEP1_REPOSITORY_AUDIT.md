# MEDHA V2 STEP 1 REPOSITORY AUDIT

This document contains a complete inspection of the current MEDHA repository prior to V2 implementation.

## 1. Repository Structure

The `engine/` directory contains five specialist engines, evaluation/testing scripts, and the new dataset.

*   `Structured_risk_enigne/`: Contains the baseline structured inference logic, pre-trained XGBoost classification models, encoders, and the OLD dataset in its `data/` subdirectory.
*   `text engine/`: Contains the Text Engine inference logic (`medha_text_engine.py`) built around a fine-tuned MuRIL classifier and pre-trained weights.
*   `voice_engine/`: Contains acoustic feature extraction logic using librosa and classification models.
*   `behaviour_engine/`: Contains rule-based mathematical scoring logic for behavioural risk metrics.
*   `fusion_engine/`: Contains the core weighted average calculation (`fusion.py`), schema definitions, engine output adapters, and numerous V1 testing/validation scripts.
*   `gru-temporal-risk/`: Contains PyTorch implementations for sequence building and GRU model evaluation.
*   `QuestionEngine/`: An interactive state machine that interfaces with victims dynamically, mapping responses to text scoring features.
*   `MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`: The newly regenerated dataset.
*   `evaluate_medha_pipeline.py`: The central orchestrator script for the old V1 experiments.

## 2. Dataset Usage Map

The dataset loading occurs in several locations. **Almost all existing scripts hard-code the old dataset path**:

*   `engine/evaluate_medha_pipeline.py` (line 34): `DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')`. Uses the `Longitudinal_Data` sheet.
*   `engine/fusion_engine/fusion_validation_pipeline.py` (line 34): Also hard-codes `MEDHA_Synthetic_1000x30-1.xlsx`.
*   `engine/fusion_engine/generate_oof_predictions.py` (line 17): Also hard-codes `MEDHA_Synthetic_1000x30-1.xlsx`.
*   `engine/QuestionEngine/patient_context.py` (line 4): Hard-codes `MEDHA_Synthetic_1000x30.xlsx` (a slightly different filename).

**Conclusion:** The new regenerated dataset (`MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`) is **NOT used anywhere yet**. All V1 scripts strictly depend on the older datasets.

## 3. Split Logic Map

**Finding: Two Inconsistent Splits Exist.**

1.  **Sequential Deterministic Split**: Found in `engine/evaluate_medha_pipeline.py` (line 43), `engine/fusion_engine/evaluate_fusion.py` (line 63). Sorts `Victim_ID`, then strictly takes the first 700 as train, the next 150 as validation, and the final 150 as test. Split assignments are *not* saved to a CSV.
2.  **Shuffled Deterministic Split**: Found in `engine/data_split.py` (line 17). Sorts `Victim_ID`, seeds the RNG to `42`, shuffles, and then splits 700/150/150. Saved to `engine/data/processed/victim_split.csv`.

**Conclusion:** Both are victim-level, but the assignments contradict each other because one uses shuffling and the other doesn't.

## 4. Structured Engine Analysis

*   **Original Target**: `Future_Escalation_Label` (Binary Classification).
*   **Model Type**: XGBoost Classifier.
*   **Feature List**: Loaded from `structured_features.pkl`. We verified it contains exactly 26 base features (`Mood`, `Stress`, `Case_Type`, etc.). It does **NOT** contain DDS lag features (`Previous_DDS`, `Rolling_DDS_Mean`, etc.).
*   **Preprocessing**: Defined in `Structured_risk_enigne/inference.py`. It maps `Episode_Severity` and one-hot encodes `Case_Type` and `Case_Stage`. This expands the 26 base features into 51 model columns.
*   **Inference Output**: `structured_risk` (the probability of escalation, bounded [0, 1]).
*   **DDS Prediction**: The frozen V1 engine does *not* predict DDS directly.
*   **step1_dds_regressor.py**: This script trains an `XGBRegressor` directly on `DDS` using the same 51 structured features output by `preprocess_structured_input`. It saves the artifact to `engine/results/structured_dds_regressor.json`.

## 5. Text Engine Analysis

*   **Model**: Google MuRIL (Multilingual).
*   **Input**: Raw textual strings (`predict_medha(text)` in `engine/text engine/medha_text_engine.py`).
*   **Output Labels**: 5 binary labels (`Distress_Label`, `Fear_Label`, `Threat_Label`, `Negative_Affect_Label`, `Urgency_Label`).
*   **Output Probabilities**: 5 float probabilities (via sigmoid).
*   **DDS Conversion**: V1 computes `text_risk` as the **unweighted arithmetic mean** of the 5 probabilities (`evaluate_medha_pipeline.py`, line 118). There is no trained regressor for Text → DDS.

## 6. Voice Engine Analysis

*   **Input**: Audio files (e.g., `.wav`).
*   **Model/Feature Extraction**: Librosa-based processing to extract `voice_distress`.
*   **Output**: A risk probability `voice_distress`.
*   **DDS Conversion**: V1 maps `voice_risk` directly to `Voice_Distress` (line 122 of `evaluate_medha_pipeline.py`). There is no trained regressor for Voice → DDS.

## 7. Behaviour Engine Analysis

*   **Formula**: `behaviour_risk = 0.40 * anomaly_score + 0.30 * clip(engagement_deviation / 3.0, 0, 1) + 0.30 * clip(inactivity_score, 0, 1)`
*   **Code Location**: `engine/fusion_engine/adapters.py` (line 148).
*   **Missing Value Handling**: Defaults missing `engagement_deviation` and `inactivity_score` to `0.0`. If `anomaly_score` is completely missing, the modality is marked as unavailable.
*   **Deviation Bug**: In the original dataset, `Engagement_Deviation` contained negative values. The actual behaviour pipeline used absolute values (`np.abs`), but the simulation in some fusion scripts didn't, causing bugs (detailed in `engine/fusion_engine/compile_report.py`).

## 8. Fusion Engine Analysis

*   **Current Formula**: Simple weighted sum of available specialist `risk` values (in `engine/fusion_engine/fusion.py`).
*   **Current Modalities**: Text, Voice, Behaviour, Structured, Temporal.
*   **Current Weights**: Located in `engine/fusion_engine/weights.py` (text: 0.25, voice: 0.15, behaviour: 0.15, structured: 0.25, temporal: 0.20). However, the actual frozen tests (`evaluate_medha_pipeline.py` line 41) use `{"text": 0.25, "voice": 0.25, "behaviour": 0.25, "structured": 0.25}`, explicitly ignoring temporal for DDS.
*   **Missing Modality Behavior**: Weights are renormalized. If Voice is missing, the weights of Text, Behaviour, and Structured proportionally scale up to sum to 1.0.
*   **DDS Calculation**: `dds = round(fused_risk * 100, 2)`.
*   **OOF Predictions**: Generated in `engine/fusion_engine/generate_oof_predictions.py` using `GroupKFold(5)` for the Structured engine, and simulated noise for the GRU engine to save time. These OOF predictions are based on the **old dataset**.
*   **Learned Fusion**: Code exists (`engine/fusion_engine/learned_fusion_experiments.py`) to train Ridge regressors over OOF predictions.
*   **Reuse**: `fusion.py` (the formula logic) and `schemas.py` are mathematically sound and should be reused. V1 testing scripts (`evaluate_fusion.py`, `generate_oof_predictions.py`) are tightly coupled to the old dataset and heuristic risk calculations, and should NOT be reused blindly.

## 9. GRU Temporal Engine Analysis

*   **Target**: `Future_Escalation_Label`.
*   **Feature Selection**: `engine/gru-temporal-risk/src/sequence_builder.py` builds sliding windows of size 7 (`window_size=7`).
*   **Input Dimensions**: Verified in `evaluate_medha_pipeline.py` (line 90): `numeric_cols[:72]`. This means the GRU blindly takes the first 72 numeric columns in the DataFrame.
*   **Data Structure**: Tensors are of shape `(samples, 7, 72)`.
*   **Preprocessing**: `engine/gru-temporal-risk/src/preprocessing.py` applies a `StandardScaler`.
*   **Architecture**: `engine/gru-temporal-risk/src/model.py` defines a 1-layer GRU, `hidden_size=64`, `dropout=0.3`.
*   **Leakage Rule Violation**: Because it takes the first 72 numeric columns in column order, if `Future_Escalation_Label` or future information happens to shift within those first 72 columns in the new dataset, leakage will occur. The explicit column list must be hardcoded.

## 10. Leakage Audit

**Are the target-derived variables used to predict current DDS?**
*   **Structured XGBoost Model**: No. The pre-trained classifier relies on 26 distinct features (verified in `structured_features.pkl`), none of which are the leaky DDS lag features.
*   **Text/Voice/Behaviour Models**: No. They rely solely on their respective signals.
*   **GRU Engine**: Yes, but legally. The GRU takes the first 72 numeric columns, which *does* include `Previous_DDS`, `Rolling_DDS_Mean`, `DDS_Slope`, and `Recent_Change_Rate`. This is acceptable because the GRU's task is predicting *future* escalation using *past* data, making these valid historical indicators for the temporal model.
*   **Conclusion**: There is no direct leakage from target-derived variables into the current DDS prediction path in the core engines, but the GRU's column-index-based feature selection is highly fragile.

## 11. Artifact Dependency Map

*   **Structured Engine**: Depends on `xgboost_model.pkl`, `case_encoder.pkl`, `episode_mapping.pkl`, `model_columns.pkl`, `structured_features.pkl`, `threshold.pkl`.
*   **Text Engine**: Depends on MuRIL weights in `Models/medha_final_model/`.
*   **Voice Engine**: Depends on artifacts in `voice_engine/models/`.
*   **Behaviour Engine**: Depends on `medha_scoring_artifacts.joblib`.
*   **GRU Engine**: Depends on `best_gru_model.pth`, `scaler.joblib`, `calibrator.joblib`.
*   **Fusion Engine**: Depends on the outputs of the adapters, which in turn depend on the inference scripts of the specialist engines above.

## 12. V1 vs V2 Boundary

V1 artifacts, scripts, and older datasets must be preserved completely. The boundary will be established by creating isolated scripts for V2.

*   **Preserve**: All existing pre-trained artifacts (`.pkl`, `.pth`, `.joblib`, `.json`), the V1 dataset (`MEDHA_Synthetic_1000x30-1.xlsx`), and the core `engine` logic folders (`Structured_risk_enigne`, `text engine`, `voice_engine`, `behaviour_engine`, `gru-temporal-risk`, `QuestionEngine`).
*   **Require V2 Changes**: We need a completely isolated V2 pipeline. We should create `v2_data_split.py`, `v2_specialist_regressors.py` (to replace heuristic risk rules with proper DDS regressors), `v2_fusion_training.py`, and `v2_gru_training.py`.
*   **Potentially Obsolete**: The heuristic risk generation logic embedded within `evaluate_medha_pipeline.py` (e.g., taking the mean of 5 text probabilities) is obsolete for V2, as we are required to train proper regressors.

## 13. Recommended Next Implementation Step

1.  **V2 Data Splitting**: Write a dedicated script (`engine/v2_data_split.py`) that loads the new regenerated dataset (`MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx`) and saves a single, authoritative, victim-level split to a CSV. All subsequent V2 scripts will rely exclusively on this CSV.
