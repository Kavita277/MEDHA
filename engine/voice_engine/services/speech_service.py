from faster_whisper import WhisperModel


# ==========================================
# LOAD WHISPER MODEL
# ==========================================

model = WhisperModel(

    "base",

    device="cpu",

    compute_type="int8"

)


# ==========================================
# TRANSCRIBE AUDIO
# ==========================================

def transcribe_audio(
    audio_path: str
):

    """
    Transcribes an audio file using Faster-Whisper.

    Returns:
        transcript
        detected language
        language probability
    """

    try:

        segments, info = model.transcribe(

            audio_path,

            beam_size=5

        )


        transcript = ""


        for segment in segments:

            transcript += (

                segment.text + " "

            )


        return {

            "transcript":

                transcript.strip(),


            "language":

                info.language,


            "language_probability":

                round(

                    float(
                        info.language_probability
                    ),

                    4
                )
        }


    except Exception as e:

        return {

            "transcript":

                "",


            "language":

                None,


            "language_probability":

                0.0,


            "error":

                str(e)
        }