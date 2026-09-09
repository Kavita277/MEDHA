import os
import sys
import pandas as pd
import numpy as np
import json

# Ensure the repository root is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 1. Import the official entry point
from engine.v2.medha_v2_pipeline import MedhaV2Pipeline
from engine.v2.priority_triage import TriageEngine

def generate_mock_backend_data() -> pd.DataFrame:
    """
    Constructs a mock longitudinal DataFrame.
    In a real backend, this data would be supplied by the production database.
    """
    # We need at least 8 rows to get a GRU prediction on the 8th row (using 7 historical steps)
    n_rows = 8
    data = {
        "Victim_ID": ["V_EXAMPLE"] * n_rows,
        "Timepoint": list(range(1, n_rows + 1)),
    }
    
    # Generate all GRU features to ensure no KeyErrors
    with open("engine/models/v2/gru_sequences/feature_config.json", "r") as f:
        gru_feats = json.load(f)["feature_whitelist"]
        for feat in gru_feats:
            if feat not in data:
                data[feat] = np.random.uniform(0, 1, n_rows)
                
    # Generate all Structured features to ensure no KeyErrors
    with open("engine/models/v2/v2_structured_dds_features.json", "r") as f:
        struct_feats = json.load(f)["features"]
        for feat in struct_feats:
            if feat not in data:
                data[feat] = np.random.uniform(0, 1, n_rows)

    # Optional Modality Flags (MUST exist in DataFrame to avoid pipeline AttributeError)
    data["Text_Available"] = [1.0] * n_rows
    data["Voice_Available"] = [1.0] * n_rows
    
    # Intentionally do NOT include Actual_DDS, Future_Escalation_Label, etc.
    return pd.DataFrame(data)

def main():
    print("Loading MEDHA V2 Pipeline...")
    # 2. Pipeline initialization (automatically loads all frozen weights and configs)
    pipeline = MedhaV2Pipeline()
    triage = TriageEngine()
    
    # 3. DataFrame construction
    print("Fetching backend data...")
    df = generate_mock_backend_data()
    
    # 4. Inference
    print("Running end-to-end inference...")
    predictions_df = pipeline.predict_v2(df)
    
    # 5. Engineering Demonstration: Apply Priority Triage
    print("Applying engineering priority triage...")
    final_df = triage.evaluate(predictions_df)
    
    # 6. Reading the strictly required downstream outputs
    print("\n--- FINAL BACKEND OUTPUT ---")
    latest_observation = final_df.iloc[-1]
    
    fusion_dds = latest_observation["Fusion_DDS_Prediction"]
    temporal_risk = latest_observation["Temporal_Risk_Score"]
    temporal_avail = latest_observation["Temporal_Available"]
    future_flag = latest_observation["Future_Escalation_Flag"]
    priority = latest_observation["Priority_Level"]
    
    print(f"Current DDS (Fusion): {fusion_dds:.2f}")
    print(f"GRU Future Risk Probability: {temporal_risk:.4f} (Available: {temporal_avail})")
    print(f"Future Escalation Flag (>=0.75): {future_flag}")
    print(f"Downstream Priority (Engineering Only): {priority}")

if __name__ == "__main__":
    main()
