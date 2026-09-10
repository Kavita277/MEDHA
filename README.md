# MEDHA V2

MEDHA V2 is an advanced, multi-modal machine-learning risk prediction system. It assesses both the **Current Distress (DDS)** and the **Future Escalation Risk** of individuals based on longitudinal historical data. The models evaluate Structured data, Text data (MuRIL embeddings), Voice data (Acoustic profiles), and Behavioural app interactions to form a holistic picture, remaining robust even when unstructured modalities are missing.

---

## 1. What does the pipeline produce?

The pipeline evaluates an individual's ongoing case history and outputs:
1. **Current DDS (0-100)**: A precise numeric estimation of current distress using an XGBoost Fusion Engine applied to all available modalities.
2. **Future Risk Probability (0-1)**: The likelihood of case escalation in the near future, determined by a PyTorch GRU model analyzing the trailing 7-step history.
3. **Availability Flags**: Indicators of whether adequate history or unstructured signals were present.

---

## 2. Quickstart: Backend Entry Point

The singular official runtime entry point for backend integration is `MedhaV2Pipeline`.

**Initialization**:
```python
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

# The pipeline automatically discovers and loads all frozen models internally.
pipeline = MedhaV2Pipeline()
```

**Providing Input Data**:
The pipeline requires a standard Pandas DataFrame containing the required longitudinal features. 
**Crucial Requirement**: The DataFrame MUST explicitly include the `Text_Available` and `Voice_Available` boolean/float indicator columns (as 1.0 or 0.0), even if all text/voice signal columns are blank. 

**Execution & Output**:
```python
# Pass the complete DataFrame
output_df = pipeline.predict_v2(input_df)

# Read the newly appended columns
fusion_dds = output_df["Fusion_DDS_Prediction"]
temporal_risk = output_df["Temporal_Risk_Score"]

# Optionally, apply engineering triage rules
from engine.v2.priority_triage import TriageEngine
triage = TriageEngine()
final_df = triage.evaluate(output_df)
```

See [backend_inference_example.py](docs/examples/backend_inference_example.py) for a complete working example.

---

## 3. Frozen Artifacts

All models are fully trained, strictly evaluated on a sealed test set, and **frozen**. You must never retrain these models in a production environment. 
* All frozen weights, configs, and preprocessors live securely in: `engine/models/`

---

## 4. Documentation & Architecture

Comprehensive technical documentation is maintained in the `docs/` directory:
* **Architecture**: [`MEDHA_V2_ARCHITECTURE.md`](docs/MEDHA_V2_ARCHITECTURE.md)
* **Model Configurations**: [`MEDHA_V2_MODEL_CARD.md`](docs/MEDHA_V2_MODEL_CARD.md)
* **Performance Metrics**: [`MEDHA_V2_RESULTS.md`](docs/MEDHA_V2_RESULTS.md)
* **Input DataFrame Schema**: [`MEDHA_V2_DATA_CONTRACT.md`](docs/MEDHA_V2_DATA_CONTRACT.md)
* **Integration API Rules**: [`MEDHA_V2_API_HANDOFF.md`](docs/MEDHA_V2_API_HANDOFF.md)
* **Reproducibility/Environment**: [`MEDHA_V2_REPRODUCIBILITY.md`](docs/MEDHA_V2_REPRODUCIBILITY.md)
* **Directory Governance**: [`MEDHA_V2_REPO_GUIDE.md`](docs/MEDHA_V2_REPO_GUIDE.md)
* **Runtime Verification**: [`MEDHA_V2_STEP17C_BACKEND_VERIFICATION.md`](docs/MEDHA_V2_STEP17C_BACKEND_VERIFICATION.md)

---

## 5. Testing

The repository contains an exhaustive suite of unit and integration tests (223+ passing tests).
To run the full test suite in your local environment:
```bash
python -m pytest engine/tests/
```

---

## 6. Repository Layout

```text
MEDHA/
├── README.md                 # This file
├── docs/                     # DOCUMENTATION: Architecture, APIs, Hand-off guides
│   └── examples/             # DOCUMENTATION: Backend inference mock scripts
├── engine/
│   ├── v2/                   # RUNTIME: Pipeline logic and feature whitelist policies
│   ├── models/               # FROZEN: Locked serializers, JSONs, PTH checkpoints
│   ├── tests/                # TESTS: Pytest unit and integration test suite
│   ├── legacy_v1/            # ARCHIVE / HISTORICAL: V1 legacy models (Do not use)
│   ├── gru-temporal-risk/    # ARCHIVE / HISTORICAL: V1 legacy models (Do not use)
│   └── fusion_engine/        # ARCHIVE / HISTORICAL: V2 experimental development
└── outputs/                  # REFERENCE: Cached inference and diagnostic metrics
```

**WARNING**: The `legacy_v1/`, `gru-temporal-risk/`, and `fusion_engine/` directories are archived purely for historical record tracking the migration path from V1 to V2. **They must never be used in a production pipeline.**