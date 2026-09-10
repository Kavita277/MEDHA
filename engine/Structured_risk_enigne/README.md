# MEDHA Structured Risk Engine

The Structured Risk Engine is the backbone of the MEDHA architecture. It evaluates structured demographic, legal, and historical tabular data (e.g., court delays, previous threats, demographic vulnerability) using an XGBoost model.

## Codebase File Directory
- **`inference.py`**: The core operational script. Contains `structured_risk_inference()`, which loads the XGBoost model, applies pre-processing, and calculates the risk score.
- **`MEDHA_Structured_Risk_Engine_Work_Log.md`**: Detailed documentation on how the synthetic dataset was generated, how the model was trained, and the baseline metrics.
- **`longitudinal_data.ipynb`**: The Jupyter notebook used to train the XGBoost model and generate the longitudinal feature engineering.
- **`Models/`**: Contains the saved `.json` or `.joblib` XGBoost model weights and scalers.
- **`data/`**: The synthetic datasets (`MEDHA_Synthetic_1000x30...`) used for testing.

## Integration Guide (For Backend Developers)

This engine is **fully built and ready for integration**.

You can directly call the inference function by passing a Pandas DataFrame row containing the structured features for a victim at a specific timepoint.

```python
import pandas as pd
from Structured_risk_enigne.inference import structured_risk_inference

# 1. Prepare your structured data as a DataFrame row
victim_data = pd.DataFrame([{
    "Age": 34,
    "Income_Level": 1,
    "Severity_of_Incident": 3,
    "FIR_Delay_Days": 14,
    # ... include all necessary structured columns
}])

# 2. Run inference
structured_risk_score = structured_risk_inference(victim_data)
# Returns a float [0, 1] representing the risk probability

# 3. Pass to Fusion Engine
# fusion_input.structured = adapt_structured_output(structured_risk_score)
```
