"""
MEDHA Voice Engine Adapter
==========================

Thin integration adapter connecting conversational audio to the existing
frozen MEDHA Voice Engine.

ABSOLUTE ARCHITECTURAL PRINCIPLES:
1. Validates that the input is an existing audio file.
2. Defers processing to `engine/voice_engine/voice_engine.py`.
3. Converts Voice Engine raw outputs into the exact 5 canonical features
   required by V2 using the deterministic mapping established in
   `engine/voice_engine/main.py`.
4. Populates `MedhaState.voice_features`.
5. Gracefully handles missing/invalid audio (availability = 0.0, None values)
   without throwing exceptions.
6. Does NOT invoke the V2 Voice Tabular DDS prediction.
"""

from typing import Optional
import os
import sys
from pathlib import Path

from chatbot.state.medha_state import MedhaState, VOICE_FEATURES
from chatbot.interfaces import VoiceAdapterProtocol


class MedhaVoiceAdapter(VoiceAdapterProtocol):
    """
    Adapter between chatbot conversational audio and the MEDHA Voice Engine.
    """

    def __init__(self, voice_engine: Optional[any] = None):
        """
        Initializes the Voice Adapter.
        Lazily loads the VoiceEngine if not provided, allowing fallback on environments
        where librosa / models are not available.
        """
        self._voice_engine = voice_engine

    def _get_voice_engine(self) -> any:
        """Lazily imports and instantiates the Voice Engine."""
        if self._voice_engine is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            voice_engine_dir = repo_root / "engine" / "voice_engine"
            if str(voice_engine_dir) not in sys.path:
                sys.path.insert(0, str(voice_engine_dir))
            
            try:
                from voice_engine import VoiceEngine
                self._voice_engine = VoiceEngine()
            except ImportError as e:
                raise RuntimeError(f"Could not load VoiceEngine: {e}")
                
        return self._voice_engine

    def process_and_update_state(
        self,
        state: MedhaState,
        audio_path: Optional[str],
    ) -> None:
        """
        Validates audio, processes via Voice Engine, and updates MedhaState.
        """
        if audio_path is None:
            return

        if not os.path.exists(audio_path):
            self._set_unavailable(state)
            return

        try:
            engine = self._get_voice_engine()
            voice_result = engine.analyze(audio_path)
            
            # Map features according to established engine/voice_engine/main.py logic
            emotions = voice_result["emotion_probabilities"]
            voice_distress = voice_result["voice_distress"]
            acoustic_indicator = voice_result["acoustic_indicator"]
            
            acoustic_features = voice_result["acoustic_features"]
            speech_rate_wpm = acoustic_features.get("speaking_rate", 0.0)
            
            # Speech Rate Deviation
            speech_rate_deviation = round(abs(speech_rate_wpm - 150) / 150, 4)
            speech_rate_deviation = min(speech_rate_deviation, 1.0)
            
            # Energy Deviation
            energy_deviation = round(min(acoustic_features.get("rms_energy", 0.0) * 50, 1.0), 4)
            
            # Pause Ratio
            pause_ratio = 0.0
            
            state.voice_features["Voice_Distress"] = float(voice_distress)
            state.voice_features["Pause_Ratio"] = float(pause_ratio)
            state.voice_features["Speech_Rate_Deviation"] = float(speech_rate_deviation)
            state.voice_features["Energy_Deviation"] = float(energy_deviation)
            state.voice_features["Acoustic_Indicator"] = float(acoustic_indicator)
            
            state.set_modality_availability("voice", 1.0)
            
        except Exception:
            # Fallback for invalid audio, Librosa errors, unsupported format, missing models, etc.
            self._set_unavailable(state)

    def _set_unavailable(self, state: MedhaState) -> None:
        """Sets all voice features to None and marks modality as unavailable."""
        for feat in VOICE_FEATURES:
            state.voice_features[feat] = None
        state.set_modality_availability("voice", 0.0)
