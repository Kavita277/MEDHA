# MEDHA V2 Data Contract

This document explicitly defines the schema of the longitudinal input DataFrame required by the MEDHA V2 pipeline, `MedhaV2Pipeline.predict_v2(df)`.

## 1. Temporal & Identity Requirements

| Column | Type | Required? | Description |
| :--- | :--- | :--- | :--- |
| `Victim_ID` | String | **YES** | Unique identifier used strictly to group historical sequences for the GRU. |
| `Timepoint` | Int / Float | **YES** | Temporal ordering variable used to sequentially sort data prior to GRU windowing. |

## 2. Modality Features

### Definitions
* **Required Columns**: The schema columns must exist in the DataFrame, even if all values are empty.
* **Availability**: Determines whether a modality actually contains signal for a specific observation.
* **Column existence != modality availability.**

### Structured (Always Required)
42 numeric columns perfectly matching the canonical `v2_structured_dds_features.json` configuration. 
* **Missing Behavior**: NaNs are permitted. The preprocessor handles them automatically (median for continuous, mode/custom encodings for categorical).
* **Availability**: Conceptually always available. `Struct_Available` is hardcoded to `1.0` internally.

### Behaviour (Always Required)
10 numeric columns representing usage logs matching `v2_behaviour_dds_features.json`.
* **Missing Behavior**: NaNs are permitted and handled by the specialized imputer.
* **Availability**: Conceptually always available. `Behav_Available` is hardcoded to `1.0` internally.

### Text (Required Columns, Required Availability)
5 numeric MuRIL-derived columns (e.g., `Text_Distress`, `Fear`).
* **Missing Behavior**: Columns must exist in the DataFrame. However, if a given row lacks text data, the values can be NaN.
* **Availability Flags**: `Text_Available` is **REQUIRED**. Completely omitting the column will trigger an `AttributeError` during the `.fillna(0)` pipeline sequence. It must be explicitly passed as `1.0` or `0.0`.

### Voice (Required Columns, Required Availability)
5 numeric acoustic columns (e.g., `Voice_Distress`, `Pause_Ratio`).
* **Missing Behavior**: Columns must exist. Values can be NaN.
* **Availability Flags**: `Voice_Available` is **REQUIRED** for the same reason. It must be explicitly passed as `1.0` or `0.0`.

### GRU Sequence (Implicit Requirement)
57 exact columns matching `feature_whitelist`. These heavily overlap with the Structured, Text, Voice, and Behaviour features defined above.
* **Missing Behavior**: Any NaN or Infinite value in these 57 features is explicitly pre-filled with `0.0` before creating the final tensor matrix to ensure safe PyTorch tensor conversion.

## 3. GRU Historical Requirements

The GRU is designed to predict future escalation by analyzing sequential history. 

* **History Length**: The pipeline enforces a strict 7-timestep trailing window (`[i-7 : i]`).
* **Insufficient History**: If a particular `Victim_ID` has fewer than 7 preceding timesteps in the provided DataFrame, the GRU cannot construct a valid tensor.
* **Fallback Behavior**: In cases of insufficient history, the pipeline handles this gracefully:
  - `Temporal_Risk_Score` returns `NaN`.
  - `Temporal_Available` returns `0`.
  - The Current DDS (Fusion prediction) is entirely unaffected and continues to function normally.
