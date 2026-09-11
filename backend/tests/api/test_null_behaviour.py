import uuid
import pytest
from backend.persistence.models.session import SessionModel, SessionStatus
from backend.services.prediction_service import generate_predictions
from backend.persistence.models.prediction_result import PredictionResultModel

def _create_mock_session_no_behaviour(db_session, test_case):
    session_id = uuid.uuid4()
    mock_state_snapshot = {
        "victim_id": str(test_case.victim_id),
        "session_id": str(session_id),
        "timepoint": 1,
        "structured_features": {
            "Safety": 8.0,
            "Engagement_Score": None,
            "Engagement_Deviation": None
        },
        "text_features": {
            "Text_Distress": 0.5,
            "Fear": 0.5,
            "Threat_Context": 0.5,
            "Negative_Affect": 0.5,
            "Urgency": 0.5
        },
        "voice_features": {
            "Voice_Distress": 0.5,
            "Pause_Ratio": 0.5,
            "Speech_Rate_Deviation": 0.5,
            "Energy_Deviation": 0.5,
            "Acoustic_Indicator": 0.5
        },
        "modality_availability": {
            "structured": 1.0,
            "text": 1.0,
            "voice": 1.0
            # behaviour is missing
        }
    }
    
    session_model = SessionModel(
        id=session_id,
        case_id=test_case.id,
        session_identifier=str(session_id),
        timepoint=1,
        status=SessionStatus.ACTIVE.value,
        state_snapshot=mock_state_snapshot
    )
    db_session.add(session_model)
    db_session.commit()
    db_session.refresh(session_model)
    return session_model


def test_prediction_without_behaviour(db_session, test_case):
    """
    TEST 1: Structured + Text + Voice + Behaviour unavailable -> prediction succeeds
    TEST 2: Behaviour unavailable -> Behav_Pred is null
    TEST 3: Behaviour unavailable -> Fusion does NOT crash
    TEST 4: Successful Fusion -> Future Risk proceeds (handled inside pipeline)
    TEST 5: Successful prediction -> result persists to DB
    TEST 7: No fabricated Behaviour -> behav_available remains false
    """
    session = _create_mock_session_no_behaviour(db_session, test_case)
    
    # Generate prediction. This previously crashed with TypeError.
    prediction: PredictionResultModel = generate_predictions(db_session, test_case.id, timepoint=1)
    
    # TEST 1 & 3: It did not crash.
    assert prediction is not None
    
    # TEST 5: Persists to DB
    assert prediction.id is not None
    
    # TEST 7: behav_available is false
    assert prediction.behav_available is False
    assert prediction.text_available is True
    assert prediction.voice_available is True
    
    # TEST 2: Behav_Pred is null
    assert prediction.behav_pred is None
    
    # Fusion is computed
    assert prediction.fusion_dds_prediction is not None
    assert prediction.triage_level != "UNKNOWN"


def test_therapist_endpoint_sees_prediction(client, therapist_token_headers, db_session, test_case):
    """
    TEST 6: Therapist results endpoint -> results_available = true when a valid prediction exists
    """
    # Create the prediction by running it first
    _create_mock_session_no_behaviour(db_session, test_case)
    generate_predictions(db_session, test_case.id, timepoint=1)
    
    # Now use the therapist API
    response = client.get(
        f"/api/v1/therapist/cases/{test_case.id}/results",
        headers=therapist_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["results_available"] is True
    assert data["fusion_dds_prediction"] is not None
    
    # Verify specialists block
    specialists = data["specialists"]
    assert specialists["behav_available"] is False
    assert specialists["behav_pred"] is None
    assert specialists["behav_blocked"] is True
