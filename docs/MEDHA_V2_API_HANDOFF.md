# Backend Integration

## Official Entry Point

The singular official entry point for backend integration is the `MedhaV2Pipeline` class located in `engine/v2/medha_v2_pipeline.py`.

```python
import pandas as pd
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

# 1. Initialize Pipeline (Loads all frozen models automatically)
pipeline = MedhaV2Pipeline()

# 2. Run Inference
output_df = pipeline.predict_v2(input_df)
```

## Input

The `predict_v2()` method strictly requires a Pandas DataFrame. 

**IMPORTANT: The following DataFrame is illustrative only and is NOT the complete production schema. The authoritative feature definitions are stored in the corresponding frozen feature configuration files.**

```python
import pandas as pd
import numpy as np

# Example Input Structure (Simplified)
input_df = pd.DataFrame({
    # Identity & Time
    "Victim_ID": ["V123", "V123"],
    "Timepoint": [1, 2],
    
    # 42 Structured Features (Example subset)
    "Age": [34, 34],
    "Incident_Type": ["Assault", "Assault"],
    
    # 5 Text Features (Can be NaN)
    "Text_Distress": [np.nan, 0.85],
    
    # 5 Voice Features (Can be NaN)
    "Voice_Distress": [np.nan, np.nan],
    
    # 10 Behaviour Features
    "App_Interaction_Duration": [12.4, 4.5],
    
    # REQUIRED Modality Flags (MUST BE SUPPLIED explicitly as 1.0 or 0.0)
    "Text_Available": [0.0, 1.0],
    "Voice_Available": [0.0, 0.0]
})
```

## Processing Flow

Inside `predict_v2()`, the data securely flows through:
1. **Specialist Models**: The input features are partitioned and fed into four parallel specialized preprocessing pipelines and models (Structured, Text, Voice, Behaviour).
2. **Fusion**: The specialist predictions and availability flags are combined. If a modality is missing, it is zeroed out. The XGBoost meta-learner constructs the **Current DDS**.
3. **GRU**: Separately, the data is grouped by `Victim_ID`, ordered by `Timepoint`, and a strict 7-timestep historical window is sliced for the PyTorch GRU to produce the **Future Risk**.

## Output

The `predict_v2()` method returns a copy of the input DataFrame with the following exact fields appended:

| Field Name | Description |
| :--- | :--- |
| `Struct_Pred` | Structured baseline prediction |
| `Struct_Available` | Hardcoded to 1.0 |
| `Text_Pred` | Text prediction (or NaN if unavailable) |
| `Text_Available` | Derived text availability flag (1.0 or 0.0) |
| `Voice_Pred` | Voice prediction (or NaN if unavailable) |
| `Voice_Available` | Derived voice availability flag (1.0 or 0.0) |
| `Behav_Pred` | Behaviour prediction |
| `Behav_Available` | Hardcoded to 1.0 |
| **`Fusion_DDS_Prediction`** | The final integrated Current DDS score (0-100) |
| **`Temporal_Risk_Score`** | The final Future Risk probability (0-1), or NaN |
| `Temporal_Available` | 1 if sufficient history existed, 0 otherwise |
| `Future_Escalation_Flag` | 1 (High Risk) or 0 (Safe) based on the 0.75 threshold |

**Explicit Note**: Priority/Triage categorizations (High, Medium, Low) are **NOT** returned directly by `predict_v2()`. They exist only as a separate demonstration component in `engine/v2/priority_triage.py`. 

## Backend Rules

To maintain the mathematical integrity, compliance, and strict leakage protection of MEDHA V2, backend engineers must strictly adhere to the following rules:

1. **NEVER** retrain models in the backend.
2. **NEVER** modify frozen model files (Pickles, JSONs, PyTorch checkpoints).
3. **NEVER** change feature order in the JSON configurations.
4. **NEVER** use V1 models or code (e.g., `engine/gru-temporal-risk/`).
5. **NEVER** pass target columns (e.g., labels) to the inference function.
6. **NEVER** bypass availability flags by hardcoding NaNs as valid signal inputs.
7. **NEVER** use `Current DDS` (or derived moving averages) as a GRU input.
8. **NEVER** alter decision thresholds casually without formal recalibration.
