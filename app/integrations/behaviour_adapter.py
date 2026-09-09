import sys
import os

BEHAVIOUR_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/behaviour_engine"))
if BEHAVIOUR_ENGINE_DIR not in sys.path:
    sys.path.insert(0, BEHAVIOUR_ENGINE_DIR)

class BehaviourAdapter:
    def __init__(self):
        self.score_one_day = None
        self.DailyFeaturesIn = None
        self.error = None
        try:
            os.environ["MEDHA_ARTIFACTS_PATH"] = os.path.join(BEHAVIOUR_ENGINE_DIR, "medha_scoring_artifacts.joblib")
            from medha_scoring_api import load_artifacts, score_one_day, DailyFeaturesIn
            self.score_one_day = score_one_day
            self.DailyFeaturesIn = DailyFeaturesIn
            load_artifacts()
        except Exception as e:
            self.error = str(e)
            print(f"BehaviourAdapter failed to load: {e}")

    def predict(self, patient_id: str, payload_dict: dict):
        if not self.score_one_day:
            raise RuntimeError(f"Behaviour Engine is not available due to initialization error: {self.error}")
            
        # Extract features if nested
        features = payload_dict.get("features", payload_dict)
        
        # Map UI payload to DailyFeaturesIn
        mapped_payload = {
            "day_index": features.get("day_index", 1),
            "completion_baseline_z": features.get("completion_baseline_z", features.get("social_isolation", 0.0)),
            "latency_baseline_z": features.get("latency_baseline_z", features.get("response_latency", 0.0)),
            "question_skip_rate": features.get("question_skip_rate", features.get("session_skip_rate", 0.0)),
            "session_duration_baseline_z": features.get("session_duration_baseline_z", features.get("duration_z_score", 0.0)),
            "response_length_baseline_z": features.get("response_length_baseline_z", 0.0),
            "missed_checkins": int(features.get("missed_checkins", features.get("missed_sessions", 0)))
        }
        
        payload = self.DailyFeaturesIn(**mapped_payload)
        res = self.score_one_day(patient_id, payload)
        # return dict, mapping attributes properly
        return {
            "anomaly_score": res.anomaly_score,
            "engagement_deviation": res.engagement_deviation,
            "inactivity_score": res.inactivity_score,
            "behavioral_risk_score": res.behavioral_risk_score,
            "triage_status": res.triage_status
        }
