# MEDHA Behaviour Engine

The Behaviour Engine analyzes interaction metadata (e.g., missed check-ins, engagement deviation over time, response latency) to quantify behavioural changes that often precede psychological escalation or distress.

## Codebase File Directory
- **`medha_scoring_api.py`**: A deployment-ready wrapper that exposes the behaviour scoring logic (potentially via a FastAPI/Flask endpoint format).
- **`medha_scoring_pipeline_corrected.py`**: The core operational script that actually runs the rules-based or learned pipeline to compute the `behaviour_risk` score.
- **`MEDHA_Behaviour_Engine_Complete_Summary.md`**: Extensive documentation covering the correlation anomalies and the sign-direction handling (e.g., why a drop in engagement increases clinical risk but mathematically lowered it in earlier prototypes).
- **`MEDHA_scored_test_set.csv`**: A snapshot of the validation outputs.
- **`medha_scoring_artifacts.joblib` & `gru_behavioral_tensor.npy`**: Stored models, tensors, and artifacts used for historical behaviour mapping.

## Integration Guide (For Backend Developers)

This engine is **fully built and ready for integration**.

You should call the scoring pipeline by passing the relevant behavioral metadata for the victim.

```python
from behaviour_engine.medha_scoring_api import calculate_behaviour_risk

# 1. Prepare behavioral data (e.g., from your database)
behaviour_data = {
    "Engagement_Deviation": -2.5,
    "Missed_Checkin": 1,
    "Response_Latency": 24.5
}

# 2. Run inference
behaviour_risk_score = calculate_behaviour_risk(behaviour_data)
# Returns a float [0, 1] representing the behavioural risk

# 3. Pass to Fusion Engine
# fusion_input.behaviour = adapt_behaviour_output(behaviour_risk_score)
```
*Note: Ensure you are passing the correct data formats as required by the `calculate_behaviour_risk` function parameters.*
