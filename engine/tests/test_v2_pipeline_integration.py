import os
import sys
import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, roc_auc_score

# Ensure engine is in path
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from engine.v2.medha_v2_pipeline import MedhaV2Pipeline

@pytest.fixture(scope="module")
def pipeline():
    return MedhaV2Pipeline(engine_dir=ENGINE_DIR)

@pytest.fixture(scope="module")
def test_data():
    csv_path = os.path.join(ENGINE_DIR, "data", "processed", "v2_longitudinal_split.csv")
    df = pd.read_csv(csv_path)
    # We only care about the test split to verify against canonical results
    return df[df["Split"] == "test"].copy().reset_index(drop=True)

def test_pipeline_instantiation(pipeline):
    """Verify that all models load correctly."""
    assert pipeline.struct_model is not None
    assert pipeline.text_model is not None
    assert pipeline.voice_model is not None
    assert pipeline.behav_model is not None
    assert pipeline.fusion_model is not None
    assert pipeline.gru_model is not None

def test_pipeline_predictions(pipeline, test_data):
    """Run pipeline on 4,500 test rows and verify outputs."""
    out_df = pipeline.predict_v2(test_data)
    
    assert "Fusion_DDS_Prediction" in out_df.columns
    assert "Temporal_Risk_Score" in out_df.columns
    assert "Future_Escalation_Flag" in out_df.columns
    
    assert len(out_df) == 4500
    
    # Check no NaN in Fusion
    assert not out_df["Fusion_DDS_Prediction"].isna().any()
    
    # Check that Temporal_Risk_Score is NaN where timepoints < 8 (i.e. i < 7)
    # For 150 victims with 30 rows each, the first 7 rows per victim (1050 rows total) should be NaN
    # The remaining 23 rows per victim (3450 rows total) should be not NaN
    assert out_df["Temporal_Risk_Score"].isna().sum() == 1050
    assert out_df["Temporal_Risk_Score"].notna().sum() == 3450
    
    # Verify Fusion matches canonical test performance exactly (MAE 5.9537)
    # Note: wait, Candidate C MAE was 5.9537 in Step 10C.
    mae = mean_absolute_error(out_df["Actual_DDS" if "Actual_DDS" in out_df.columns else "DDS"], out_df["Fusion_DDS_Prediction"])
    assert np.isclose(mae, 5.9537, atol=1e-4), f"Fusion MAE {mae} != 5.9537"
    
    # Verify GRU matches canonical test performance exactly (ROC AUC 0.7953)
    # Only for valid rows and non-NaN labels
    valid_gru = out_df[(out_df["Temporal_Available"] == 1) & (out_df["Future_Escalation_Label"].notna())]
    auc = roc_auc_score(valid_gru["Future_Escalation_Label"], valid_gru["Temporal_Risk_Score"])
    assert np.isclose(auc, 0.7953, atol=1e-4), f"GRU AUC {auc} != 0.7953"

if __name__ == "__main__":
    pytest.main([__file__])
