import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from backend.integrations.medha_v2 import run_v2_inference

def test_run_v2_inference_handles_missing_data():
    # Mock the V2 pipeline
    with patch("backend.integrations.medha_v2.get_v2_pipeline") as mock_get_pipeline:
        mock_pipeline = MagicMock()
        mock_pipeline.structured_features = ["age", "gender"]
        mock_pipeline.text_features = ["sentiment"]
        mock_pipeline.voice_features = ["pitch"]
        mock_pipeline.behaviour_features_all = ["App_Interaction_Duration"]
        mock_pipeline.fusion_features = ["fusion_f1"]
        mock_pipeline.gru_features = ["gru_f1"]
        
        mock_get_pipeline.return_value = mock_pipeline
        
        # Mock predict_v2 to return a dummy dataframe
        import pandas as pd
        dummy_result = pd.DataFrame([{
            "Struct_Pred": 0.85,
            "Text_Pred": np.nan,
            "Voice_Pred": np.nan,
            "Behav_Pred": 0.70,
            "Fusion_DDS_Prediction": 82.5,
            "Temporal_Risk_Score": 0.95,
            "Temporal_Available": 1,
            "Future_Escalation_Flag": 1
        }])
        mock_pipeline.predict_v2.return_value = dummy_result

        # Run inference with missing features
        input_features = {
            "age": 30,
            # Missing gender, sentiment, pitch
            "App_Interaction_Duration": 120.0
        }
        
        result = run_v2_inference("victim-123", 1, input_features)
        
        assert result["Struct_Pred"] == 0.85
        assert result["Text_Pred"] is None
        assert result["Voice_Pred"] is None
        assert result["Behav_Pred"] == 0.70
        assert result["Fusion_DDS_Prediction"] == 82.5
        assert result["Temporal_Risk_Score"] == 0.95
        assert result["Temporal_Available"] == 1
        assert result["Future_Escalation_Flag"] == 1

        # Verify DataFrame passed to predict_v2
        args, _ = mock_pipeline.predict_v2.call_args
        df_passed = args[0]
        
        assert "Victim_ID" in df_passed.columns
        assert df_passed["Victim_ID"].iloc[0] == "victim-123"
        assert pd.isna(df_passed["gender"].iloc[0]) # Missing handled as np.nan
        assert df_passed["age"].iloc[0] == 30
