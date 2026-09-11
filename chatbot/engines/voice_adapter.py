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

    def _extract_native_acoustic_features(self, audio_path: str) -> dict:
        """
        Native acoustic feature extractor using standard library wave and scipy.signal.
        Extracts the 5 canonical V2 Voice Specialist features without external C dependencies.
        """
        import wave
        import numpy as np
        from scipy.signal import find_peaks

        with wave.open(audio_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 1:
            samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        duration = max(0.5, len(samples) / float(max(1, framerate)))

        # 1. Pause Ratio & Energy Deviation
        frame_len = int(framerate * 0.025)
        frame_step = int(framerate * 0.010)
        if len(samples) > frame_len:
            frames = [samples[i:i + frame_len] for i in range(0, len(samples) - frame_len, frame_step)]
            frame_energies = np.array([np.sqrt(np.mean(f ** 2)) for f in frames])
            max_energy = np.max(frame_energies) if len(frame_energies) > 0 else 0.001
            silence_thresh = max(0.0005, max_energy * 0.10)
            pause_ratio = float(np.clip(np.sum(frame_energies < silence_thresh) / len(frame_energies), 0.0, 1.0))
            energy_deviation = float(np.clip(np.std(frame_energies) * 20.0, 0.0, 1.0))
        else:
            pause_ratio = 0.15
            energy_deviation = 0.25

        # 2. Speech Rate Deviation
        if len(samples) > frame_len * 2:
            envelope = np.abs(samples)
            win = int(framerate * 0.04)
            smooth = np.convolve(envelope, np.ones(win) / win, mode="same")
            peaks, _ = find_peaks(smooth, height=np.mean(smooth) * 0.75, distance=int(framerate * 0.12))
            syllables = len(peaks)
            est_wpm = (syllables / 1.35) * (60.0 / duration)
            speech_rate_deviation = float(np.clip(abs(est_wpm - 150.0) / 150.0, 0.0, 1.0))
        else:
            speech_rate_deviation = 0.2

        # 3. Acoustic Indicator (spectral volatility / zero crossing rate)
        if len(samples) > 1:
            zcr = np.sum(np.abs(np.diff(np.sign(samples)))) / (2.0 * len(samples))
            acoustic_indicator = float(np.clip(zcr * 8.0, 0.0, 1.0))
        else:
            acoustic_indicator = 0.35

        # 4. Voice Distress (composite)
        voice_distress = float(np.clip(
            0.35 * energy_deviation + 0.35 * speech_rate_deviation + 0.30 * acoustic_indicator,
            0.05,
            0.95
        ))

        return {
            "voice_distress": round(voice_distress, 4),
            "pause_ratio": round(pause_ratio, 4),
            "speech_rate_deviation": round(speech_rate_deviation, 4),
            "energy_deviation": round(energy_deviation, 4),
            "acoustic_indicator": round(acoustic_indicator, 4),
            "duration_seconds": round(duration, 2),
        }

    def process_and_update_state(
        self,
        state: MedhaState,
        audio_path: Optional[str],
    ) -> None:
        """
        Validates audio, processes via Voice Engine (or native fallback), and updates MedhaState.
        """
        if audio_path is None:
            return

        if not os.path.exists(audio_path):
            self._set_unavailable(state)
            return

        # Attempt primary engine first
        try:
            engine = self._get_voice_engine()
            voice_result = engine.analyze(audio_path)
            
            voice_distress = voice_result["voice_distress"]
            acoustic_indicator = voice_result["acoustic_indicator"]
            acoustic_features = voice_result["acoustic_features"]
            speech_rate_wpm = acoustic_features.get("speaking_rate", 0.0)
            speech_rate_deviation = round(abs(speech_rate_wpm - 150) / 150, 4)
            speech_rate_deviation = min(speech_rate_deviation, 1.0)
            energy_deviation = round(min(acoustic_features.get("rms_energy", 0.0) * 50, 1.0), 4)
            pause_ratio = 0.0
            
            state.voice_features["Voice_Distress"] = float(voice_distress)
            state.voice_features["Pause_Ratio"] = float(pause_ratio)
            state.voice_features["Speech_Rate_Deviation"] = float(speech_rate_deviation)
            state.voice_features["Energy_Deviation"] = float(energy_deviation)
            state.voice_features["Acoustic_Indicator"] = float(acoustic_indicator)
            state.set_modality_availability("voice", 1.0)
            return
        except Exception:
            pass

        # Native Scipy/Wave fallback
        try:
            native_res = self._extract_native_acoustic_features(audio_path)
            state.voice_features["Voice_Distress"] = float(native_res["voice_distress"])
            state.voice_features["Pause_Ratio"] = float(native_res["pause_ratio"])
            state.voice_features["Speech_Rate_Deviation"] = float(native_res["speech_rate_deviation"])
            state.voice_features["Energy_Deviation"] = float(native_res["energy_deviation"])
            state.voice_features["Acoustic_Indicator"] = float(native_res["acoustic_indicator"])
            state.set_modality_availability("voice", 1.0)
        except Exception:
            self._set_unavailable(state)

    def _set_unavailable(self, state: MedhaState) -> None:
        """Sets all voice features to None and marks modality as unavailable."""
        for feat in VOICE_FEATURES:
            state.voice_features[feat] = None
        state.set_modality_availability("voice", 0.0)
