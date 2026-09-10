import os
import joblib
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


MODELS_DIR = os.path.join(
    BASE_DIR,
    "models"
)


# ============================================================
# LOAD TRAINED MODELS
# ============================================================

VOICE_DISTRESS_MODEL_PATH = os.path.join(
    MODELS_DIR,
    "voice_distress_model.joblib"
)


ACOUSTIC_INDICATOR_MODEL_PATH = os.path.join(
    MODELS_DIR,
    "acoustic_indicator_model.joblib"
)


VOICE_DISTRESS_FEATURES_PATH = os.path.join(
    MODELS_DIR,
    "voice_distress_feature_names.joblib"
)


ACOUSTIC_INDICATOR_FEATURES_PATH = os.path.join(
    MODELS_DIR,
    "acoustic_indicator_feature_names.joblib"
)


print("Loading trained MEDHA Voice models...")


voice_distress_model = joblib.load(
    VOICE_DISTRESS_MODEL_PATH
)


acoustic_indicator_model = joblib.load(
    ACOUSTIC_INDICATOR_MODEL_PATH
)


voice_distress_feature_names = joblib.load(
    VOICE_DISTRESS_FEATURES_PATH
)


acoustic_indicator_feature_names = joblib.load(
    ACOUSTIC_INDICATOR_FEATURES_PATH
)


print("Voice Distress Model loaded successfully.")
print("Acoustic Indicator Model loaded successfully.")


# ============================================================
# EMOTION KEY NORMALIZATION
# ============================================================

def normalize_emotions(emotions):

    """
    Converts runtime emotion keys into the feature names
    expected by the trained models.

    Runtime engine:
        ang, sad, neu, hap

    Training dataset:
        angry, sad, neutral, happy
    """

    normalized = {

        "angry": float(
            emotions.get(
                "ang",
                emotions.get(
                    "angry",
                    0.0
                )
            )
        ),

        "sad": float(
            emotions.get(
                "sad",
                0.0
            )
        ),

        "neutral": float(
            emotions.get(
                "neu",
                emotions.get(
                    "neutral",
                    0.0
                )
            )
        ),

        "happy": float(
            emotions.get(
                "hap",
                emotions.get(
                    "happy",
                    0.0
                )
            )
        )
    }


    return normalized


# ============================================================
# VOICE DISTRESS PREDICTION
# ============================================================

def predict_voice_distress(

    emotions,
    speaking_rate,
    pitch_mean,
    pitch_std,
    rms

):

    normalized_emotions = normalize_emotions(
        emotions
    )


    feature_data = {

        "angry":

            normalized_emotions[
                "angry"
            ],


        "sad":

            normalized_emotions[
                "sad"
            ],


        "neutral":

            normalized_emotions[
                "neutral"
            ],


        "happy":

            normalized_emotions[
                "happy"
            ],


        "speaking_rate":

            float(
                speaking_rate
            ),


        "pitch_mean":

            float(
                pitch_mean
            ),


        "pitch_std":

            float(
                pitch_std
            ),


        "rms":

            float(
                rms
            )
    }


    input_data = pd.DataFrame(

        [feature_data],

        columns=voice_distress_feature_names
    )


    prediction = voice_distress_model.predict(
        input_data
    )[0]


    # Keep output between 0 and 1
    prediction = max(
        0.0,
        min(
            1.0,
            float(prediction)
        )
    )


    return round(
        prediction,
        4
    )


# ============================================================
# ACOUSTIC INDICATOR PREDICTION
# ============================================================

def predict_acoustic_indicator(

    speaking_rate,
    pitch_mean,
    pitch_std,
    rms

):

    feature_data = {

        "speaking_rate":

            float(
                speaking_rate
            ),


        "pitch_mean":

            float(
                pitch_mean
            ),


        "pitch_std":

            float(
                pitch_std
            ),


        "rms":

            float(
                rms
            )
    }


    input_data = pd.DataFrame(

        [feature_data],

        columns=acoustic_indicator_feature_names
    )


    prediction = acoustic_indicator_model.predict(
        input_data
    )[0]


    # Keep output between 0 and 1
    prediction = max(
        0.0,
        min(
            1.0,
            float(prediction)
        )
    )


    return round(
        prediction,
        4
    )