import os
import joblib
import numpy as np
import librosa

from pathlib import Path


class VoiceEngine:

    def __init__(self):

        print("Loading trained MEDHA voice models...")

        BASE_DIR = Path(__file__).resolve().parent
        MODELS_DIR = BASE_DIR / "models"

        # ==========================================
        # LOAD TRAINED MODELS
        # ==========================================

        self.voice_distress_model = joblib.load(
            MODELS_DIR / "voice_distress_model.joblib"
        )

        self.acoustic_indicator_model = joblib.load(
            MODELS_DIR / "acoustic_indicator_model.joblib"
        )

        # ==========================================
        # LOAD FEATURE NAMES
        # ==========================================

        self.voice_distress_feature_names = joblib.load(
            MODELS_DIR / "voice_distress_feature_names.joblib"
        )

        self.acoustic_indicator_feature_names = joblib.load(
            MODELS_DIR / "acoustic_indicator_feature_names.joblib"
        )

        print("Voice Distress Model Features:")
        print(self.voice_distress_feature_names)

        print("Acoustic Indicator Model Features:")
        print(self.acoustic_indicator_feature_names)

        print("MEDHA trained voice models loaded successfully.")

    # ==========================================
    # MAIN ANALYSIS FUNCTION
    # ==========================================

    def analyze(self, audio_path):

        # ==========================================
        # LOAD AUDIO
        # ==========================================

        y, sr = librosa.load(
            audio_path,
            sr=None,
            mono=True
        )

        duration_seconds = round(
            librosa.get_duration(
                y=y,
                sr=sr
            ),
            4
        )

        # ==========================================
        # BASIC ACOUSTIC FEATURES
        # ==========================================

        rms = float(
            np.mean(
                librosa.feature.rms(
                    y=y
                )
            )
        )

        zero_crossing_rate = float(
            np.mean(
                librosa.feature.zero_crossing_rate(
                    y
                )
            )
        )

        # ==========================================
        # PITCH EXTRACTION
        # ==========================================

        pitches, magnitudes = librosa.piptrack(
            y=y,
            sr=sr
        )

        pitch_values = pitches[
            magnitudes > np.median(magnitudes)
        ]

        pitch_values = pitch_values[
            pitch_values > 0
        ]

        if len(pitch_values) > 0:

            pitch_mean = float(
                np.mean(
                    pitch_values
                )
            )

            pitch_std = float(
                np.std(
                    pitch_values
                )
            )

        else:

            pitch_mean = 0.0
            pitch_std = 0.0

        # ==========================================
        # SPEAKING RATE ESTIMATION
        # ==========================================

        speaking_rate = self.estimate_speaking_rate(
            y,
            sr,
            duration_seconds
        )

        # ==========================================
        # EMOTION PROBABILITIES
        # ==========================================

        emotion_probabilities = self.estimate_emotions(
            y,
            sr,
            rms,
            pitch_mean,
            pitch_std
        )

        # ==========================================
        # CREATE EXACT MODEL INPUT
        #
        # IMPORTANT:
        # Voice distress model was trained on:
        #
        # angry
        # sad
        # neutral
        # happy
        # speaking_rate
        # pitch_mean
        # pitch_std
        # rms
        #
        # DO NOT ADD EXTRA FEATURES HERE
        # ==========================================

        voice_distress_feature_map = {

            "angry":
                emotion_probabilities["angry"],

            "sad":
                emotion_probabilities["sad"],

            "neutral":
                emotion_probabilities["neutral"],

            "happy":
                emotion_probabilities["happy"],

            "speaking_rate":
                speaking_rate,

            "pitch_mean":
                pitch_mean,

            "pitch_std":
                pitch_std,

            "rms":
                rms
        }

        # ==========================================
        # CREATE FEATURE VECTOR
        # USING EXACT TRAINING ORDER
        # ==========================================

        voice_distress_input = np.array([

            [
                voice_distress_feature_map[
                    feature
                ]

                for feature in
                self.voice_distress_feature_names
            ]

        ])

        # ==========================================
        # PREDICT VOICE DISTRESS
        # ==========================================

        voice_distress = float(

            self.voice_distress_model.predict(
                voice_distress_input
            )[0]

        )

        # Keep prediction between 0 and 1

        voice_distress = float(

            np.clip(
                voice_distress,
                0,
                1
            )

        )

        # ==========================================
        # ACOUSTIC INDICATOR MODEL INPUT
        #
        # Trained on:
        #
        # speaking_rate
        # pitch_mean
        # pitch_std
        # rms
        # ==========================================

        acoustic_feature_map = {

            "speaking_rate":
                speaking_rate,

            "pitch_mean":
                pitch_mean,

            "pitch_std":
                pitch_std,

            "rms":
                rms
        }

        acoustic_input = np.array([

            [
                acoustic_feature_map[
                    feature
                ]

                for feature in
                self.acoustic_indicator_feature_names
            ]

        ])

        # ==========================================
        # PREDICT ACOUSTIC INDICATOR
        # ==========================================

        acoustic_indicator = float(

            self.acoustic_indicator_model.predict(
                acoustic_input
            )[0]

        )

        acoustic_indicator = float(

            np.clip(
                acoustic_indicator,
                0,
                1
            )

        )

        # ==========================================
        # MODEL CONFIDENCE
        #
        # Currently based on strongest emotion
        # probability.
        # ==========================================

        confidence = float(

            max(
                emotion_probabilities.values()
            )

        )

        # ==========================================
        # RETURN RESULT
        # ==========================================

        return {

            "voice_distress":
                round(
                    voice_distress,
                    4
                ),

            "confidence":
                round(
                    confidence,
                    4
                ),

            "emotion_probabilities":
                emotion_probabilities,

            "acoustic_features": {

                "duration_seconds":
                    round(
                        duration_seconds,
                        4
                    ),

                "rms_energy":
                    round(
                        rms,
                        6
                    ),

                "pitch_mean":
                    round(
                        pitch_mean,
                        4
                    ),

                "pitch_std":
                    round(
                        pitch_std,
                        4
                    ),

                "zero_crossing_rate":
                    round(
                        zero_crossing_rate,
                        6
                    ),

                "speaking_rate":
                    round(
                        speaking_rate,
                        4
                    )
            },

            "acoustic_indicator":
                round(
                    acoustic_indicator,
                    4
                )
        }

    # ==========================================
    # SPEAKING RATE ESTIMATION
    # ==========================================

    def estimate_speaking_rate(
        self,
        y,
        sr,
        duration
    ):

        if duration <= 0:

            return 0.0

        # Estimate speech activity using onset detection

        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=sr
        )

        estimated_syllables = len(
            onset_frames
        )

        # Convert estimated syllables into
        # approximate words
        #
        # Average English word ≈ 1.5 syllables

        estimated_words = (
            estimated_syllables / 1.5
        )

        speaking_rate = (

            estimated_words /
            duration

        ) * 60

        return float(

            np.clip(
                speaking_rate,
                0,
                300
            )

        )

    # ==========================================
    # EMOTION ESTIMATION
    #
    # Temporary heuristic mapping.
    #
    # Your trained distress model then combines
    # these emotion values with acoustic features.
    # ==========================================

    def estimate_emotions(
        self,
        y,
        sr,
        rms,
        pitch_mean,
        pitch_std
    ):

        # ==========================================
        # NORMALIZED SIGNAL CHARACTERISTICS
        # ==========================================

        energy_score = min(
            rms * 50,
            1.0
        )

        pitch_variation_score = min(
            pitch_std / 300,
            1.0
        )

        pitch_score = min(
            pitch_mean / 400,
            1.0
        )

        # ==========================================
        # EMOTION HEURISTICS
        #
        # These produce normalized probabilities
        # required by the trained model.
        # ==========================================

        angry = (

            0.5 * energy_score

            +

            0.3 * pitch_variation_score

            +

            0.2 * pitch_score

        )

        sad = (

            0.6 * (1 - energy_score)

            +

            0.2 * (1 - pitch_score)

            +

            0.2 * (1 - pitch_variation_score)

        )

        happy = (

            0.4 * energy_score

            +

            0.3 * pitch_score

            +

            0.3 * pitch_variation_score

        )

        neutral = 0.5

        # ==========================================
        # NORMALIZE
        # ==========================================

        emotion_values = np.array([

            angry,
            sad,
            neutral,
            happy

        ])

        emotion_values = np.clip(
            emotion_values,
            0.001,
            None
        )

        emotion_values = (

            emotion_values /
            np.sum(emotion_values)

        )

        return {

            "angry":
                round(
                    float(emotion_values[0]),
                    4
                ),

            "sad":
                round(
                    float(emotion_values[1]),
                    4
                ),

            "neutral":
                round(
                    float(emotion_values[2]),
                    4
                ),

            "happy":
                round(
                    float(emotion_values[3]),
                    4
                )
        }