import os
import sys

# Test Text Engine
def test_text():
    try:
        sys.path.insert(0, r"d:\Projects\SIH\MEDHA\engine\text engine")
        from medha_text_engine import medha_text_engine
        print("Text Engine: Loaded")
    except Exception as e:
        print("Text Engine: FAILED ->", str(e))

def test_voice():
    try:
        sys.path.insert(0, r"d:\Projects\SIH\MEDHA\engine\voice_engine")
        from voice_engine import VoiceEngine
        ve = VoiceEngine()
        print("Voice Engine: Loaded")
    except Exception as e:
        print("Voice Engine: FAILED ->", str(e))

def test_behaviour():
    try:
        sys.path.insert(0, r"d:\Projects\SIH\MEDHA\engine\behaviour_engine")
        from medha_scoring_api import load_artifacts, score_one_day, DailyFeaturesIn
        os.environ["MEDHA_ARTIFACTS_PATH"] = r"d:\Projects\SIH\MEDHA\engine\behaviour_engine\medha_scoring_artifacts.joblib"
        load_artifacts()
        print("Behaviour Engine: Loaded")
    except Exception as e:
        print("Behaviour Engine: FAILED ->", str(e))

def test_structured():
    try:
        sys.path.insert(0, r"d:\Projects\SIH\MEDHA\engine\Structured_risk_enigne")
        from inference import structured_engine_api
        print("Structured Engine: Loaded")
    except Exception as e:
        print("Structured Engine: FAILED ->", str(e))

def test_temporal():
    try:
        sys.path.insert(0, r"d:\Projects\SIH\MEDHA\engine\gru-temporal-risk")
        os.chdir(r"d:\Projects\SIH\MEDHA\engine\gru-temporal-risk")
        from src.inference_api import load_assets
        load_assets()
        print("Temporal Engine: Loaded")
    except Exception as e:
        print("Temporal Engine: FAILED ->", str(e))

if __name__ == "__main__":
    test_text()
    test_voice()
    test_behaviour()
    test_structured()
    test_temporal()
