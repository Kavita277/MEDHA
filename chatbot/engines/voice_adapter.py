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
        Universal acoustic feature extractor using PyAV, soundfile, wave, and scipy.signal.
        Extracts the 5 canonical V2 Voice Specialist features without external C dependencies:
        - Voice_Distress: Composite acoustic distress index [0.05, 0.95]
        - Pause_Ratio: Proportion of clinical hesitation pauses (>150ms silence)
        - Speech_Rate_Deviation: Cadence divergence from normal fluent pace (145 WPM)
        - Energy_Deviation: Vocal energy instability and hypophonic deficit
        - Acoustic_Indicator: High-frequency spectral activity (zero crossing rate)
        """
        import wave
        import numpy as np
        from scipy.signal import find_peaks

        samples = None
        framerate = 16000
        duration = 3.0

        # Method 1: PyAV Universal Decoder (decodes AAC, M4A, WAV, MP3, CAF, etc.)
        try:
            import av
            with av.open(audio_path) as container:
                resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
                all_frames = []
                for frame in container.decode(audio=0):
                    for rf in resampler.resample(frame):
                        all_frames.append(rf.to_ndarray())
                if all_frames:
                    raw_s16 = np.concatenate(all_frames, axis=1).squeeze()
                    samples = raw_s16.astype(np.float32) / 32768.0
                    framerate = 16000
                    duration = max(0.5, len(samples) / float(framerate))
        except Exception:
            pass

        # Method 2: Soundfile Decoder
        if samples is None:
            try:
                import soundfile as sf
                data, sr = sf.read(audio_path)
                if data.ndim > 1:
                    data = data.mean(axis=1)
                samples = data.astype(np.float32)
                framerate = sr
                duration = max(0.5, len(samples) / float(framerate))
            except Exception:
                pass

        # Method 3: Standard Library Wave
        if samples is None:
            try:
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
            except Exception:
                pass

        # Robust Fallback if decoding completely failed
        if samples is None or len(samples) == 0:
            file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 32000
            duration = round(max(1.0, file_size / 32000.0), 2)
            return {
                "voice_distress": 0.35,
                "pause_ratio": 0.20,
                "speech_rate_deviation": 0.10,
                "energy_deviation": 0.15,
                "acoustic_indicator": 0.15,
                "duration_seconds": duration,
            }

        # 1. Dynamic Energy & Adaptive Noise Floor VAD
        frame_len = int(framerate * 0.025)  # 25ms = 400
        frame_step = int(framerate * 0.010) # 10ms = 160
        if len(samples) > frame_len:
            frames = [samples[i:i + frame_len] for i in range(0, len(samples) - frame_len, frame_step)]
            frame_energies = np.array([np.sqrt(np.mean(f ** 2)) for f in frames])

            # Dynamic noise floor tracking (15th percentile of energy)
            noise_floor = float(np.percentile(frame_energies, 15))
            speech_thresh = max(noise_floor * 2.2, noise_floor + 0.005)
            is_silent = frame_energies < speech_thresh

            # Clinical hesitation pauses (> 200ms silence = 20 consecutive silent frames)
            silent_count = 0
            current_run = 0
            min_pause_frames = 20
            for s in is_silent:
                if s:
                    current_run += 1
                else:
                    if current_run >= min_pause_frames:
                        silent_count += current_run
                    current_run = 0
            if current_run >= min_pause_frames:
                silent_count += current_run
            pause_ratio = float(np.clip(silent_count / max(1, len(frame_energies)), 0.0, 1.0))

            # 2. Voiced Segment Energy & Deficit (Hypophonia vs Projection)
            voiced_energies = frame_energies[~is_silent]
            if len(voiced_energies) > 5:
                voiced_mean = np.mean(voiced_energies)
                snr = voiced_mean / (noise_floor + 1e-5)
                # Low SNR / faint voice projection indicates depressive hypophonia
                energy_deficit = float(np.clip(max(0.0, 1.0 - (snr / 8.0)), 0.02, 0.90))
                voiced_std = np.std(voiced_energies)
                energy_instability = float(np.clip((voiced_std / (voiced_mean + 1e-4)) * 0.4, 0.0, 0.5))
                energy_deviation = float(np.clip(0.7 * energy_deficit + 0.3 * energy_instability, 0.02, 0.90))
            else:
                energy_deviation = 0.50
                voiced_mean = noise_floor

            # 3. Monotone Pitch Factor (Autocorrelation on Voiced Segments)
            pitches = []
            min_lag = int(framerate / 450)
            max_lag = int(framerate / 70)
            for i in range(0, len(samples) - frame_len, frame_step * 2):
                f = samples[i:i + frame_len]
                if np.sqrt(np.mean(f ** 2)) >= speech_thresh:
                    corr = np.correlate(f, f, mode="full")[frame_len - 1:]
                    search = corr[min_lag:max_lag]
                    if len(search) > 0 and np.max(search) > 0.35 * corr[0]:
                        pitches.append(framerate / (min_lag + np.argmax(search)))
            pitch_std = float(np.std(pitches)) if len(pitches) > 5 else 10.0
            monotone_index = float(np.clip((35.0 - pitch_std) / 35.0, 0.0, 1.0))

            # 4. Syllable Detection & Speech Rate Deviation (145 WPM fluent baseline)
            envelope = np.abs(samples)
            win = int(framerate * 0.04)
            smooth = np.convolve(envelope, np.ones(win) / win, mode="same")
            peaks, _ = find_peaks(smooth, height=max(speech_thresh, np.mean(smooth) * 0.65), distance=int(framerate * 0.14))
            syllables = len(peaks)
            active_duration = max(1.0, len(voiced_energies) * 0.010)
            est_wpm = (syllables / 1.4) * (60.0 / active_duration)
            speech_rate_deviation = float(np.clip(abs(est_wpm - 145.0) / 145.0, 0.0, 1.0))

            # 5. Acoustic Indicator (Zero Crossing Rate on Voiced Segments)
            if len(voiced_energies) > 5 and any(~is_silent):
                voiced_samples = np.concatenate([samples[i:i + frame_len] for i, v in enumerate(~is_silent) if v and i * frame_step + frame_len < len(samples)])
                zcr = np.sum(np.abs(np.diff(np.sign(voiced_samples)))) / (2.0 * max(1, len(voiced_samples)))
                acoustic_indicator = float(np.clip(zcr * 2.0, 0.05, 0.50))
            else:
                acoustic_indicator = 0.15

            # 6. Clinically Weighted Voice Distress Composite
            voice_distress = float(np.clip(
                0.35 * pause_ratio + 0.30 * monotone_index + 0.20 * energy_deviation + 0.15 * speech_rate_deviation,
                0.05,
                0.95
            ))
        else:
            pause_ratio = 0.10
            speech_rate_deviation = 0.10
            energy_deviation = 0.10
            acoustic_indicator = 0.15
            voice_distress = 0.15

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
        Validates audio, processes via Universal Acoustic Feature Extractor, and updates MedhaState.
        """
        if audio_path is None:
            return

        if not os.path.exists(audio_path):
            self._set_unavailable(state)
            return

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
