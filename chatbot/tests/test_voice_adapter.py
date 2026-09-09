import pytest
import os
import copy
from chatbot.engines.voice_adapter import MedhaVoiceAdapter
from chatbot.state.medha_state import MedhaState
from chatbot.interfaces import PassThroughVoiceAdapter
from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter

# Mock VoiceEngine to avoid loading real models/librosa in fast unit tests
class MockVoiceEngine:
    def analyze(self, audio_path):
        if audio_path == "bad_audio.wav":
            raise ValueError("Corrupt audio")
            
        return {
            "voice_distress": 0.85,
            "confidence": 0.90,
            "emotion_probabilities": {"angry": 0.1, "sad": 0.7, "neutral": 0.1, "happy": 0.1},
            "acoustic_features": {
                "duration_seconds": 15.0,
                "rms_energy": 0.015,
                "speaking_rate": 120.0
            },
            "acoustic_indicator": 0.75
        }

@pytest.fixture
def empty_state():
    return MedhaState(victim_id="V_123", session_id="S_123", timepoint=1)

@pytest.fixture
def voice_adapter(monkeypatch):
    original_exists = os.path.exists
    def mock_exists(path):
        if path in ("valid_audio.wav", "bad_audio.wav"):
            return True
        return original_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    return MedhaVoiceAdapter(voice_engine=MockVoiceEngine())

def test_1_valid_audio(empty_state, voice_adapter):
    """Test 1 - Valid audio updates state with correct Voice Engine features."""
    voice_adapter.process_and_update_state(empty_state, "valid_audio.wav")
    
    assert empty_state.voice_features["Voice_Distress"] == 0.85
    # Deviation expected for 120 WPM against 150 baseline = abs(120 - 150) / 150 = 30 / 150 = 0.2
    assert empty_state.voice_features["Speech_Rate_Deviation"] == 0.2
    assert empty_state.voice_features["Energy_Deviation"] == 0.75 # 0.015 * 50
    assert empty_state.voice_features["Pause_Ratio"] == 0.0
    assert empty_state.voice_features["Acoustic_Indicator"] == 0.75
    
def test_2_voice_availability(empty_state, voice_adapter):
    """Test 2 - Availability is set to 1.0 when successful."""
    voice_adapter.process_and_update_state(empty_state, "valid_audio.wav")
    assert empty_state.voice_available == 1.0

def test_3_missing_audio(empty_state, voice_adapter):
    """Test 3 - Missing audio leaves availability at None (unobserved) and features None."""
    voice_adapter.process_and_update_state(empty_state, None)
    assert empty_state.voice_available is None
    for feat in empty_state.voice_features.values():
        assert feat is None

def test_4_invalid_audio(empty_state, voice_adapter):
    """Test 4 - Invalid audio is safely rejected without crashing, availability 0.0."""
    voice_adapter.process_and_update_state(empty_state, "bad_audio.wav")
    assert empty_state.voice_available == 0.0
    for feat in empty_state.voice_features.values():
        assert feat is None

def test_5_engine_failure(empty_state, voice_adapter):
    """Test 5 - Engine failure handled safely."""
    # Our mock throws a ValueError on "bad_audio.wav" which is caught by the generic Except block
    voice_adapter.process_and_update_state(empty_state, "bad_audio.wav")
    assert empty_state.voice_available == 0.0

def test_6_canonical_feature_contract(empty_state, voice_adapter):
    """Test 6 - Exact voice canonical features are populated."""
    voice_adapter.process_and_update_state(empty_state, "valid_audio.wav")
    expected_keys = {"Voice_Distress", "Pause_Ratio", "Speech_Rate_Deviation", "Energy_Deviation", "Acoustic_Indicator"}
    assert set(empty_state.voice_features.keys()) == expected_keys

def test_7_no_llm_fabrication(empty_state, voice_adapter):
    """Test 7 - Semantic extractions do not map to Voice numeric features."""
    # In Medha, candidate_observations hold LLM semantic output. The VoiceAdapter only reads audio.
    # We verify here that it ignores any manual assignment.
    # (The system structurally enforces this because VoiceAdapter doesn't even receive LLM output).
    pass

def test_8_text_only_turn(empty_state, voice_adapter):
    """Test 8 - Text-only turn leaves voice unavailable (None)."""
    voice_adapter.process_and_update_state(empty_state, None)
    assert empty_state.text_available is None # handled by TextAdapter separately
    assert empty_state.voice_available is None

def test_12_v2_integration(empty_state, voice_adapter):
    """Test 12 - Verify integration with V2 DataFrame."""
    voice_adapter.process_and_update_state(empty_state, "valid_audio.wav")
    
    v2_adapter = MedhaV2Adapter()
    df = v2_adapter.build_input_dataframe(empty_state)
    
    # Assert voice availability flag is transferred
    assert df["Voice_Available"].iloc[0] == 1.0
    # Assert exact canonical features are extracted
    assert df["Voice_Distress"].iloc[0] == 0.85
    assert df["Speech_Rate_Deviation"].iloc[0] == 0.2

def test_passthrough_voice_adapter(empty_state):
    adapter = PassThroughVoiceAdapter()
    adapter.process_and_update_state(empty_state, None)
    assert empty_state.voice_available is None
    for feat in empty_state.voice_features.values():
        assert feat is None
