import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any

# Ensure engine is in path to import MedhaV2Pipeline
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
engine_dir = os.path.join(repo_root, "engine")
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

# Singleton pipeline instance to avoid reloading models on every call
_v2_pipeline_instance = None

def get_v2_pipeline() -> MedhaV2Pipeline:
    global _v2_pipeline_instance
    if _v2_pipeline_instance is None:
        _v2_pipeline_instance = MedhaV2Pipeline()
    return _v2_pipeline_instance

def run_v2_inference(victim_id: str, timepoint: int, current_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs the exact DataFrame expected by the frozen V2 pipeline,
    executes inference, and returns the predictions safely.
    """
    pipeline = get_v2_pipeline()

    # 1. Start with a copy of features
    row_data = current_features.copy()
    
    for k, v in row_data.items():
        if v is None:
            row_data[k] = np.nan
    
    # 2. Inject structural identifiers
    row_data["Victim_ID"] = victim_id
    row_data["Timepoint"] = timepoint

    # 3. Create DataFrame
    df = pd.DataFrame([row_data])

    # 4. Fill missing expected columns with np.nan
    # This prevents KeyError in the frozen pipeline
    all_expected_features = set()
    all_expected_features.update(pipeline.structured_features)
    all_expected_features.update(pipeline.text_features)
    all_expected_features.update(pipeline.voice_features)
    all_expected_features.update(pipeline.behaviour_features_all)
    all_expected_features.update(pipeline.fusion_features)
    all_expected_features.update(pipeline.gru_features)
    
    for feat in all_expected_features:
        if feat not in df.columns:
            df[feat] = np.nan
            
    # Also explicitly ensure availability flags are present
    for avail_flag in ["Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"]:
        if avail_flag not in df.columns:
            df[avail_flag] = 0.0

    # 5. Run inference
    result_df = pipeline.predict_v2(df)

    # 6. Extract predictions
    pred_row = result_df.iloc[0]
    
    predictions = {
        "Struct_Pred": float(pred_row.get("Struct_Pred", np.nan)) if not pd.isna(pred_row.get("Struct_Pred")) else None,
        "Text_Pred": float(pred_row.get("Text_Pred", np.nan)) if not pd.isna(pred_row.get("Text_Pred")) else None,
        "Voice_Pred": float(pred_row.get("Voice_Pred", np.nan)) if not pd.isna(pred_row.get("Voice_Pred")) else None,
        "Behav_Pred": float(pred_row.get("Behav_Pred", np.nan)) if not pd.isna(pred_row.get("Behav_Pred")) else None,
        "Fusion_DDS_Prediction": float(pred_row.get("Fusion_DDS_Prediction", np.nan)) if not pd.isna(pred_row.get("Fusion_DDS_Prediction")) else None,
        "Temporal_Risk_Score": float(pred_row.get("Temporal_Risk_Score", np.nan)) if not pd.isna(pred_row.get("Temporal_Risk_Score")) else None,
        "Temporal_Available": int(pred_row.get("Temporal_Available", 0)),
        "Future_Escalation_Flag": int(pred_row.get("Future_Escalation_Flag", 0)) if not pd.isna(pred_row.get("Future_Escalation_Flag")) else None,
    }

    return predictions
