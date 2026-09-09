import sys
import os

VOICE_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/voice_engine"))
if VOICE_ENGINE_DIR not in sys.path:
    sys.path.insert(0, VOICE_ENGINE_DIR)

class VoiceAdapter:
    def __init__(self):
        self.engine = None
        self.error = None
        try:
            from voice_engine import VoiceEngine
            self.engine = VoiceEngine()
        except Exception as e:
            self.error = str(e)
            print(f"VoiceAdapter failed to load: {e}")

    def predict(self, audio_path: str):
        if not self.engine:
            raise RuntimeError(f"Voice Engine is not available due to initialization error: {self.error}")
        return self.engine.analyze(audio_path)
