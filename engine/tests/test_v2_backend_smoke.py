import pytest
import pandas as pd
import numpy as np
import os
import json

from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

@pytest.fixture(scope="module")
def pipeline():
    return MedhaV2Pipeline()

@pytest.fixture(scope="module")
def mock_victim_data():
    """Generates synthetic rows for a single victim representing their case history."""
    # We need 8 rows for GRU history (predict 8th row using previous 7)
    n_rows = 8
    data = {
        "Victim_ID": ["V_SMOKE"] * n_rows,
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
    
    # Ensure no target labels exist
    for forbidden in ["Actual_DDS", "Future_Escalation_Label", "Previous_DDS", "Rolling_DDS_Mean"]:
        assert forbidden not in data
        
    return pd.DataFrame(data)

def test_pipeline_import_and_load(pipeline):
    assert pipeline is not None
    assert pipeline.fusion_model is not None
    assert pipeline.gru_model is not None

def test_full_multimodal_inference(pipeline, mock_victim_data):
    df = mock_victim_data.copy()
    out_df = pipeline.predict_v2(df)
    
    # Check output columns
    assert "Struct_Pred" in out_df.columns
    assert "Struct_Available" in out_df.columns
    assert "Text_Pred" in out_df.columns
    assert "Text_Available" in out_df.columns
    assert "Voice_Pred" in out_df.columns
    assert "Voice_Available" in out_df.columns
    assert "Behav_Pred" in out_df.columns
    assert "Behav_Available" in out_df.columns
    
    assert "Fusion_DDS_Prediction" in out_df.columns
    assert "Temporal_Risk_Score" in out_df.columns
    assert "Temporal_Available" in out_df.columns
    assert "Future_Escalation_Flag" in out_df.columns
    
    # Check values
    assert not out_df["Fusion_DDS_Prediction"].isna().any()
    assert (out_df["Fusion_DDS_Prediction"] >= 0).all() and (out_df["Fusion_DDS_Prediction"] <= 100).all()
    
    # GRU check (last row has history)
    assert not pd.isna(out_df["Temporal_Risk_Score"].iloc[-1])
    assert out_df["Temporal_Available"].iloc[-1] == 1
    
    # Check vector order explicitly in the config
    assert pipeline.fusion_features == [
        "Struct_Pred", "Text_Pred", "Voice_Pred", "Behav_Pred",
        "Struct_Available", "Text_Available", "Voice_Available", "Behav_Available"
    ]

def test_missing_text_inference(pipeline, mock_victim_data):
    df = mock_victim_data.copy()
    df["Text_Available"] = 0.0
    # Also explicitly mock Text features as NaN to prove imputation works or is bypassed
    for col in pipeline.text_features:
        df[col] = np.nan
        
    out_df = pipeline.predict_v2(df)
    assert not out_df["Fusion_DDS_Prediction"].isna().any()
    assert (out_df["Text_Pred"].isna() | (out_df["Text_Pred"] == 0.0)).all() # Might be NaN or 0

def test_missing_voice_inference(pipeline, mock_victim_data):
    df = mock_victim_data.copy()
    df["Voice_Available"] = 0.0
    for col in pipeline.voice_features:
        df[col] = np.nan
        
    out_df = pipeline.predict_v2(df)
    assert not out_df["Fusion_DDS_Prediction"].isna().any()

def test_missing_text_and_voice_inference(pipeline, mock_victim_data):
    df = mock_victim_data.copy()
    df["Text_Available"] = 0.0
    df["Voice_Available"] = 0.0
    # The backend schema MUST supply these flags, so we test them being explicitly 0.
    
    out_df = pipeline.predict_v2(df)
    assert not out_df["Fusion_DDS_Prediction"].isna().any()
    assert (out_df["Text_Available"] == 0.0).all()
    assert (out_df["Voice_Available"] == 0.0).all()

def test_insufficient_history(pipeline, mock_victim_data):
    df = mock_victim_data.copy()
    df = df.iloc[:3] # Only 3 rows, not enough for 7-timestep GRU
    
    out_df = pipeline.predict_v2(df)
    assert out_df["Temporal_Available"].eq(0).all()
    assert out_df["Temporal_Risk_Score"].isna().all()
    assert out_df["Future_Escalation_Flag"].isna().all()
    
    # But Fusion DDS still works
    assert not out_df["Fusion_DDS_Prediction"].isna().any()

