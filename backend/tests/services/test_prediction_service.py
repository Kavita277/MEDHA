import pytest
import uuid
from unittest.mock import patch, MagicMock
from backend.services.prediction_service import generate_predictions

def test_generate_predictions(db_session, test_case):
    case_id = test_case.id
    timepoint = 1

    with patch("backend.services.prediction_service.get_latest_session_state") as mock_get_state, \
         patch("backend.services.prediction_service.get_behaviour_snapshot") as mock_get_behav, \
         patch("backend.services.prediction_service.run_v2_inference") as mock_run_inference:

        mock_get_state.return_value = {
            "structured_features": {"age": 25},
            "modality_availability": {"structured": 1.0}
        }
        
        mock_behav = MagicMock()
        mock_behav.app_interaction_duration = 300.0
        mock_get_behav.return_value = mock_behav
        
        mock_run_inference.return_value = {
            "Struct_Pred": 0.5,
            "Text_Pred": None,
            "Voice_Pred": None,
            "Behav_Pred": 0.6,
            "Fusion_DDS_Prediction": 75.0,
            "Temporal_Risk_Score": 0.8,
            "Temporal_Available": 1,
            "Future_Escalation_Flag": 1
        }

        prediction = generate_predictions(db_session, case_id, timepoint)

        assert prediction.case_id == case_id
        assert prediction.timepoint == timepoint
        assert prediction.struct_pred == 0.5
        assert prediction.text_pred is None
        assert prediction.fusion_dds_prediction == 75.0
        assert prediction.triage_level == "HIGH" # 75.0 is between 60 and 80
        assert prediction.struct_available is True
        assert prediction.text_available is False
        assert prediction.behav_available is True

        # Ensure run_inference was called with correctly aggregated dict
        args, _ = mock_run_inference.call_args
        features = args[2]
        assert features["age"] == 25
        assert features["App_Interaction_Duration"] == 300.0
        assert features["Struct_Available"] == 1.0
