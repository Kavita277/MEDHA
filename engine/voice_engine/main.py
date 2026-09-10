from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

import shutil
import uuid
import os

from datetime import datetime

from voice_engine import VoiceEngine
from services.speech_service import transcribe_audio


app = FastAPI(
    title="MEDHA Voice Engine",
    description="Voice emotion, acoustic signal, speech transcription and longitudinal analysis",
    version="0.8.1"
)


print("Initializing Voice Engine...")

engine = VoiceEngine()


# ==========================================
# TEMPORARY IN-MEMORY HISTORY STORAGE
# ==========================================

voice_history = {}


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {

        "message":
            "MEDHA Voice Engine is running",

        "version":
            "0.8.1"
    }


# ==========================================
# ANALYZE VOICE
# ==========================================

@app.post("/analyze-voice")
async def analyze_voice(

    patient_id: str = Form(...),

    audio: UploadFile = File(...)

):

    original_filename = audio.filename or ""

    file_extension = os.path.splitext(
        original_filename
    )[1]

    # Default extension

    if not file_extension:

        file_extension = ".wav"


    filename = f"temp_{uuid.uuid4()}{file_extension}"


    try:

        # ==========================================
        # SAVE AUDIO
        # ==========================================

        with open(
            filename,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                audio.file,
                buffer
            )


        # ==========================================
        # VOICE ANALYSIS
        # ==========================================

        voice_result = engine.analyze(
            filename
        )


        # ==========================================
        # SPEECH TRANSCRIPTION
        # ==========================================

        speech_result = transcribe_audio(
            filename
        )


        transcript = speech_result.get(
            "transcript",
            ""
        )


        # ==========================================
        # GET ACOUSTIC FEATURES
        # ==========================================

        acoustic_features = voice_result[
            "acoustic_features"
        ]


        duration = acoustic_features.get(
            "duration_seconds",
            0
        )


        # ==========================================
        # CALCULATE TRANSCRIPT SPEECH RATE
        # ==========================================

        word_count = len(
            transcript.split()
        )


        if duration > 0:

            speech_rate_wpm = round(

                (
                    word_count / duration
                ) * 60,

                2

            )

        else:

            speech_rate_wpm = 0.0


        # ==========================================
        # GET TRAINED MODEL OUTPUTS
        # ==========================================

        emotions = voice_result[
            "emotion_probabilities"
        ]


        voice_distress = voice_result[
            "voice_distress"
        ]


        acoustic_indicator = voice_result[
            "acoustic_indicator"
        ]


        voice_confidence = voice_result[
            "confidence"
        ]


        # ==========================================
        # SPEECH RATE DEVIATION
        #
        # Normal conversational speech
        # baseline ≈ 150 WPM
        # ==========================================

        speech_rate_deviation = round(

            abs(
                speech_rate_wpm - 150
            ) / 150,

            4

        )


        speech_rate_deviation = min(
            speech_rate_deviation,
            1.0
        )


        # ==========================================
        # ENERGY DEVIATION
        # ==========================================

        energy_deviation = round(

            min(

                acoustic_features[
                    "rms_energy"
                ] * 50,

                1.0

            ),

            4

        )


        # ==========================================
        # PAUSE RATIO
        #
        # Currently basic placeholder.
        # Can be improved later with VAD.
        # ==========================================

        pause_ratio = 0.0


        # ==========================================
        # VOICE FEATURES
        # ==========================================

        voice_features = {

            "voice_distress":
                voice_distress,

            "voice_confidence":
                voice_confidence,

            "pause_ratio":
                pause_ratio,

            "speech_rate_deviation":
                speech_rate_deviation,

            "energy_deviation":
                energy_deviation,

            "acoustic_indicator":
                acoustic_indicator
        }


        # ==========================================
        # FUSION FEATURES
        #
        # EXACT SCHEMA REQUIRED
        # BY MEDHA FUSION ENGINE
        # ==========================================

        fusion_features = {

            "voice_available":
                1,

            "voice_distress":
                voice_distress,

            "pause_ratio":
                pause_ratio,

            "speech_rate_deviation":
                speech_rate_deviation,

            "energy_deviation":
                energy_deviation,

            "acoustic_indicator":
                acoustic_indicator
        }


        # ==========================================
        # TIMESTAMP
        # ==========================================

        timestamp = datetime.now().isoformat()


        # ==========================================
        # FINAL RESPONSE
        # ==========================================

        response = {

            "patient_id":
                patient_id,

            "timestamp":
                timestamp,

            "voice_available":
                True,

            "voice_features":
                voice_features,

            "fusion_features":
                fusion_features,

            "speech": {

                "transcript":
                    transcript,

                "language":
                    speech_result.get(
                        "language"
                    ),

                "language_probability":
                    speech_result.get(
                        "language_probability",
                        0.0
                    ),

                "speech_rate_wpm":
                    speech_rate_wpm
            },

            "raw_features": {

                "emotion_probabilities":
                    emotions,

                "acoustic_features":
                    acoustic_features
            }
        }


        # ==========================================
        # SAVE HISTORY
        # ==========================================

        if patient_id not in voice_history:

            voice_history[
                patient_id
            ] = []


        voice_history[
            patient_id
        ].append({

            "patient_id":
                patient_id,

            "timestamp":
                timestamp,

            "fusion_features":
                fusion_features
        })


        response[
            "history_records"
        ] = len(

            voice_history[
                patient_id
            ]

        )


        return response


    except Exception as e:

        timestamp = datetime.now().isoformat()


        unavailable_response = {

            "patient_id":
                patient_id,

            "timestamp":
                timestamp,

            "voice_available":
                False,

            "voice_features": {

                "voice_distress":
                    None,

                "voice_confidence":
                    None,

                "pause_ratio":
                    None,

                "speech_rate_deviation":
                    None,

                "energy_deviation":
                    None,

                "acoustic_indicator":
                    None
            },

            "fusion_features": {

                "voice_available":
                    0,

                "voice_distress":
                    None,

                "pause_ratio":
                    None,

                "speech_rate_deviation":
                    None,

                "energy_deviation":
                    None,

                "acoustic_indicator":
                    None
            },

            "speech": {

                "transcript":
                    "",

                "language":
                    None,

                "language_probability":
                    0.0,

                "speech_rate_wpm":
                    0.0
            },

            "error":
                str(e)
        }


        return JSONResponse(

            status_code=200,

            content=unavailable_response
        )


    finally:

        if os.path.exists(
            filename
        ):

            os.remove(
                filename
            )


# ==========================================
# VOICE HISTORY
# ==========================================

@app.get("/voice-history/{patient_id}")
def get_voice_history(

    patient_id: str

):

    history = voice_history.get(

        patient_id,

        []
    )


    return {

        "patient_id":
            patient_id,

        "total_records":
            len(history),

        "history":
            history
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "service":
            "MEDHA Voice Engine",

        "version":
            "0.8.1"
    }