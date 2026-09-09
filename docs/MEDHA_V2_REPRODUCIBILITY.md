# MEDHA V2 Reproducibility

This document outlines the exact environment, artifacts, and commands required to reproduce the MEDHA V2 system behavior in a local or backend environment.

## 1. Environment

The MEDHA V2 models were trained and frozen using the following major dependencies. These are the observed frozen-build environment versions. For maximum reproducibility, match the recorded environment where available:

* **Python**: 3.14.4
* **Pandas**: 3.0.5
* **NumPy**: 2.5.2
* **Scikit-learn**: 1.9.0
* **XGBoost**: 3.4.1
* **PyTorch**: 2.13.0+cpu

## 2. Model Artifacts

The system relies strictly on the following frozen canonical artifacts located relative to the repository root:

* `engine/models/structured_dds_v2/v2_structured_dds_xgb.json`
* `engine/models/structured_dds_v2/v2_structured_dds_preprocessor.pkl`
* `engine/models/text_dds_v2/v2_text_dds_ridge_core5.pkl`
* `engine/models/text_dds_v2/v2_text_dds_preprocessor.pkl`
* `engine/models/voice_dds_v2/v2_voice_dds_ridge_core5.pkl`
* `engine/models/voice_dds_v2/v2_voice_dds_preprocessor.pkl`
* `engine/models/behaviour_dds_v2/v2_behaviour_dds_ridge_all10.pkl`
* `engine/models/behaviour_dds_v2/v2_behaviour_dds_preprocessor.pkl`
* `engine/models/v2/fusion_final/fusion_model.json`
* `engine/models/v2/gru/best_gru_model.pth`
* `engine/models/v2/gru_sequences/scaler.joblib`

## 3. Loading

The entire suite of models, preprocessors, and configurations are loaded automatically by initializing the main pipeline class. No manual instantiation of PyTorch or XGBoost objects is required by the backend developer.

```python
import pandas as pd
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

# The initialization dynamically discovers the engine/models/ directory relative to its path.
pipeline = MedhaV2Pipeline()
```

## 4. Inference

Inference is strictly executed using the `predict_v2()` method on a longitudinal Pandas DataFrame. 

```python
# df must contain Victim_ID, Timepoint, and required features
predictions_df = pipeline.predict_v2(df)

# predictions_df will contain the original columns plus:
# Fusion_DDS_Prediction, Temporal_Risk_Score, Future_Escalation_Flag
```

## 5. Tests

The repository contains an exhaustive suite of unit and integration tests covering the V2 pipeline, feature policies, data leakage guards, and missing modality fallback behavior.

To run the full test suite:
```bash
python -m pytest engine/tests/
```
**Currently verified count**: 223 tests passing.

## 6. Integrity

To guarantee that the models have not been tampered with or accidentally modified, SHA-256 hashes for canonical artifacts are generated during training. Do not modify the JSON weights or Pickle files. If any file is changed, the backend must reject the deployment.

## 7. Determinism

The MEDHA V2 architecture uses fixed random seeds (e.g., `42`) across all XGBoost training, PyTorch initializations, and data splits. Because the model weights are now completely frozen and the preprocessing uses deterministic imputation, running identical input data through `predict_v2()` will yield the exact same `Current DDS` and `Future Risk` probabilities down to floating-point precision on every run.
