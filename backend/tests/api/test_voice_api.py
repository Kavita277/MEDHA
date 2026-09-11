import uuid
import io
import json
from unittest.mock import patch, MagicMock

from backend.persistence.models.session import SessionModel, SessionStatus

def _create_mock_session(db_session, test_case):
    session_id = uuid.uuid4()
    mock_state_snapshot = {
        "victim_id": str(test_case.victim_id),
        "session_id": str(session_id),
        "timepoint": 1,
        "metadata": {"custom_flag": True},
        "voice_available": 0.5,
        "text_available": 0.5
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


def test_voice_checkin_success(client, user_token_headers, db_session, test_user, test_case):
    """
    Test 5: Existing voice functionality remains compatible.
    Test a successful voice checkin upload without providing a session_id explicitly.
    """
    with patch("backend.services.case_service.CaseService.get_active_case_for_user") as mock_get_case, \
         patch("backend.services.voice_service.MedhaVoiceAdapter") as mock_adapter_class:
        
        mock_get_case.return_value = test_case
        
        mock_adapter_instance = MagicMock()
        mock_adapter_class.return_value = mock_adapter_instance
        
        def fake_process(state, temp_path):
            state.set_modality_availability("voice", 1.0)
            
        mock_adapter_instance.process_and_update_state.side_effect = fake_process

        fake_audio = io.BytesIO(b"fake audio data")
        fake_audio.name = "test_audio.wav"

        response = client.post(
            "/api/v1/voice/checkin",
            headers=user_token_headers,
            data={"timepoint": "Day 1"},
            files={"audio_file": ("test_audio.wav", fake_audio, "audio/wav")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == str(test_case.id)
        assert data["timepoint"] == "Day 1"
        assert data["available"] == 1.0


def test_voice_checkin_with_session_restores_and_persists_state(client, user_token_headers, db_session, test_user, test_case):
    """
    TEST 1: A session with existing MedhaState receives voice input. Verify the voice pipeline receives the restored state.
    TEST 2: Voice processing changes the state. Verify the updated state is persisted.
    TEST 3: A subsequent request can restore the updated state. (Inferred by persistence)
    """
    session_model = _create_mock_session(db_session, test_case)
    
    with patch("backend.services.case_service.CaseService.get_active_case_for_user") as mock_get_case, \
         patch("backend.services.voice_service.MedhaVoiceAdapter") as mock_adapter_class:
        
        mock_get_case.return_value = test_case
        mock_adapter_instance = MagicMock()
        mock_adapter_class.return_value = mock_adapter_instance
        
        def fake_process(state, temp_path):
            # Assert state was restored correctly
            assert state.metadata.get("custom_flag") is True
            assert state.voice_available == 0.5
            
            # Change the state
            state.metadata["custom_flag"] = False
            state.metadata["new_voice_flag"] = True
            state.set_modality_availability("voice", 1.0)
            
        mock_adapter_instance.process_and_update_state.side_effect = fake_process

        fake_audio = io.BytesIO(b"fake audio data")
        fake_audio.name = "test_audio.wav"

        response = client.post(
            "/api/v1/voice/checkin",
            headers=user_token_headers,
            data={"timepoint": "Day 1", "session_id": str(session_model.id)},
            files={"audio_file": ("test_audio.wav", fake_audio, "audio/wav")}
        )

        assert response.status_code == 200
        
        # Verify persistence (TEST 2 & 3)
        db_session.refresh(session_model)
        updated_snapshot = session_model.state_snapshot
        assert updated_snapshot["metadata"]["custom_flag"] is False
        assert updated_snapshot["metadata"]["new_voice_flag"] is True
        assert updated_snapshot["voice_available"] == 1.0


def test_voice_checkin_failure_does_not_corrupt_state(client, user_token_headers, db_session, test_user, test_case):
    """
    TEST 4: Voice processing fails. Verify the previous valid state is not incorrectly overwritten.
    """
    session_model = _create_mock_session(db_session, test_case)
    # copy dict
    original_snapshot = json.loads(json.dumps(session_model.state_snapshot))
    
    with patch("backend.services.case_service.CaseService.get_active_case_for_user") as mock_get_case, \
         patch("backend.services.voice_service.MedhaVoiceAdapter") as mock_adapter_class:
        
        mock_get_case.return_value = test_case
        mock_adapter_instance = MagicMock()
        mock_adapter_class.return_value = mock_adapter_instance
        
        def fake_process_error(state, temp_path):
            state.metadata["custom_flag"] = False # Mutate it in memory
            raise ValueError("Simulated adapter failure")
            
        mock_adapter_instance.process_and_update_state.side_effect = fake_process_error

        fake_audio = io.BytesIO(b"fake audio data")
        fake_audio.name = "test_audio.wav"

        response = client.post(
            "/api/v1/voice/checkin",
            headers=user_token_headers,
            data={"timepoint": "Day 1", "session_id": str(session_model.id)},
            files={"audio_file": ("test_audio.wav", fake_audio, "audio/wav")}
        )

        assert response.status_code == 500
        
        # Verify state was NOT corrupted in the database
        db_session.refresh(session_model)
        assert session_model.state_snapshot == original_snapshot
        assert session_model.state_snapshot["metadata"]["custom_flag"] is True
