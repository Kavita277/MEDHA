import sys
import os

TEMPORAL_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/gru-temporal-risk"))
if TEMPORAL_ENGINE_DIR not in sys.path:
    sys.path.insert(0, TEMPORAL_ENGINE_DIR)

class TemporalAdapter:
    def __init__(self):
        self.predict_risk = None
        self.SequenceInput = None
        self.error = None
        original_cwd = os.getcwd()
        try:
            os.chdir(TEMPORAL_ENGINE_DIR)
            from src.inference_api import load_assets, predict_risk, SequenceInput
            load_assets()
            self.predict_risk = predict_risk
            self.SequenceInput = SequenceInput
        except Exception as e:
            self.error = str(e)
            print(f"TemporalAdapter failed to load: {e}")
        finally:
            os.chdir(original_cwd)

    def predict(self, features: list):
        if not self.predict_risk:
            raise RuntimeError(f"Temporal Engine is not available due to initialization error: {self.error}")
        req = self.SequenceInput(features=features)
        return self.predict_risk(req)
