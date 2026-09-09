"""
MEDHA V2 - Inference Input-to-Output Demonstration and Test

This test loads/generates longitudinal victim input data, passes it through the
frozen MEDHA V2 Pipeline (MedhaV2Pipeline) and Priority Triage Engine (TriageEngine),
and prints formatted summaries of the inputs and final outputs.

Usage:
    - Via pytest (with stdout enabled):
        python -m pytest -s engine/tests/test_v2_inference_io.py
    - As a standalone script:
        python engine/tests/test_v2_inference_io.py
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd

# Add repository root to path if running standalone
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from engine.v2.medha_v2_pipeline import MedhaV2Pipeline
from engine.v2.priority_triage import TriageEngine


def create_sample_input(n_rows: int = 8, victim_id: str = "VIC_DEMO_001") -> pd.DataFrame:
    """
    Constructs synthetic input data representing a patient case history over multiple timepoints.
    Requires at least 8 rows so the GRU (7-step window) can predict on the 8th row.
    """
    np.random.seed(42)
    data = {
        "Victim_ID": [victim_id] * n_rows,
        "Timepoint": list(range(1, n_rows + 1)),
    }

    # Load GRU features whitelist
    gru_cfg_path = os.path.join(REPO_ROOT, "engine", "models", "v2", "gru_sequences", "feature_config.json")
    with open(gru_cfg_path, "r") as f:
        gru_feats = json.load(f)["feature_whitelist"]
        for feat in gru_feats:
            if feat not in data:
                data[feat] = np.random.uniform(0.1, 0.9, n_rows)

    # Load Structured features
    struct_cfg_path = os.path.join(REPO_ROOT, "engine", "models", "v2", "v2_structured_dds_features.json")
    with open(struct_cfg_path, "r") as f:
        struct_feats = json.load(f)["features"]
        for feat in struct_feats:
            if feat not in data:
                data[feat] = np.random.uniform(0.1, 0.9, n_rows)

    # Modality availability flags (contract requirement)
    data["Text_Available"] = [1.0] * n_rows
    data["Voice_Available"] = [1.0] * n_rows

    return pd.DataFrame(data)


def test_inference_takes_input_and_prints_final_outputs():
    """
    Executes end-to-end V2 inference, asserts output validity, and prints detailed I/O.
    """
    print("\n" + "=" * 80)
    print("                MEDHA V2 INFERENCE: INPUT -> FINAL OUTPUT TEST")
    print("=" * 80)

    # 1. INPUT PREPARATION
    df_input = create_sample_input(n_rows=8, victim_id="VIC_DEMO_001")

    print("\n[1] INPUT DATA OVERVIEW")
    print("-" * 80)
    print(f"Total Observations (Timepoints) : {len(df_input)}")
    print(f"Total Input Columns             : {len(df_input.columns)}")
    print(f"Victim ID                       : {df_input['Victim_ID'].iloc[0]}")
    print(f"Timepoints                      : {df_input['Timepoint'].tolist()}")
    print(f"Text Available Flag             : {df_input['Text_Available'].unique().tolist()}")
    print(f"Voice Available Flag            : {df_input['Voice_Available'].unique().tolist()}")
    
    # Print sample of input features
    sample_cols = ["Victim_ID", "Timepoint", "Text_Available", "Voice_Available"]
    other_cols = [c for c in df_input.columns if c not in sample_cols][:4]
    display_cols = sample_cols + other_cols
    print("\nSample Input Rows (truncated feature subset):")
    print(df_input[display_cols].head(3).to_string(index=False))

    # 2. RUN PIPELINE INFERENCE
    print("\n" + "-" * 80)
    print("[2] EXECUTING MEDHA V2 PIPELINE & PRIORITY TRIAGE...")
    pipeline = MedhaV2Pipeline()
    triage = TriageEngine()

    predictions_df = pipeline.predict_v2(df_input)
    final_output_df = triage.evaluate(predictions_df)
    print("Inference completed successfully.")

    # 3. PRINT TIMEPOINT-BY-TIMEPOINT OUTPUT TABLE
    print("\n" + "-" * 80)
    print("[3] TIMEPOINT RESULTS TABLE")
    print("-" * 80)

    summary_columns = [
        "Timepoint",
        "Struct_Pred",
        "Text_Pred",
        "Voice_Pred",
        "Behav_Pred",
        "Fusion_DDS_Prediction",
        "Temporal_Risk_Score",
        "Priority_Level",
    ]

    # Format numeric columns for clean printing
    formatted_display = final_output_df[summary_columns].copy()
    for col in ["Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred", "Fusion_DDS_Prediction"]:
        formatted_display[col] = formatted_display[col].map(lambda x: f"{x:6.2f}" if pd.notna(x) else "   N/A")
    formatted_display["Temporal_Risk_Score"] = formatted_display["Temporal_Risk_Score"].map(
        lambda x: f"{x:6.4f}" if pd.notna(x) else "   N/A (history < 7)"
    )

    print(formatted_display.to_string(index=False))

    # 4. PRINT LATEST TIMEPOINT FINAL OUTPUT SUMMARY
    latest = final_output_df.iloc[-1]
    print("\n" + "=" * 80)
    print("                         FINAL INFERENCE OUTPUT (LATEST)")
    print("=" * 80)
    print(f"Victim ID                    : {latest['Victim_ID']}")
    print(f"Current Timepoint            : {latest['Timepoint']}")
    print(f"--------------------------------------------------------------------------------")
    print(f"Specialist 1 (Structured)   : {latest['Struct_Pred']:.2f}  (Available: {int(latest['Struct_Available'])})")
    print(f"Specialist 2 (Text)         : {latest['Text_Pred']:.2f}  (Available: {int(latest['Text_Available'])})")
    print(f"Specialist 3 (Voice)        : {latest['Voice_Pred']:.2f}  (Available: {int(latest['Voice_Available'])})")
    print(f"Specialist 4 (Behavioural)  : {latest['Behav_Pred']:.2f}  (Available: {int(latest['Behav_Available'])})")
    print(f"--------------------------------------------------------------------------------")
    print(f"CANONICAL OUTPUT 1 (Current DDS)        : {latest['Fusion_DDS_Prediction']:.2f} / 100.0")
    print(f"CANONICAL OUTPUT 2 (Future Risk Score)  : {latest['Temporal_Risk_Score']:.4f} (Flag: {int(latest['Future_Escalation_Flag'])})")
    print(f"CANONICAL OUTPUT 3 (Priority Level)     : {latest['Priority_Level']}")
    print(f"Priority Rationale                      : {latest['Priority_Rationale']}")
    print("=" * 80 + "\n")

    # 5. ASSERTIONS (Automated validation)
    assert not final_output_df["Fusion_DDS_Prediction"].isna().any(), "Fusion DDS contains NaN values"
    assert (final_output_df["Fusion_DDS_Prediction"] >= 0).all() and (final_output_df["Fusion_DDS_Prediction"] <= 100).all()
    
    # 8th row must have temporal risk
    assert not pd.isna(latest["Temporal_Risk_Score"]), "Latest row should have Temporal_Risk_Score"
    assert latest["Temporal_Available"] == 1
    assert latest["Priority_Level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]


if __name__ == "__main__":
    test_inference_takes_input_and_prints_final_outputs()
