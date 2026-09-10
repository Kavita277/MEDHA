import uuid
import io
from unittest.mock import patch, MagicMock

def test_voice_checkin_success(client, user_token_headers, db_session, test_user, test_case):
    """
    Test a successful voice checkin upload.
    """
    # Mock the case lookup to return the test_case
    with patch("backend.services.case_service.CaseService.get_active_case_for_user") as mock_get_case, \
         patch("backend.services.voice_service.MedhaVoiceAdapter") as mock_adapter_class:
        
        mock_get_case.return_value = test_case
        
        # Setup mock adapter
        mock_adapter_instance = MagicMock()
        mock_adapter_class.return_value = mock_adapter_instance
        
        # Simulate processing the audio and setting availability
        def fake_process(state, temp_path):
            state.set_modality_availability("voice", 1.0)
            
        mock_adapter_instance.process_and_update_state.side_effect = fake_process

        # Create a dummy audio file
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
        assert "message" in data

        # Verify adapter was called
        mock_adapter_instance.process_and_update_state.assert_called_once()
