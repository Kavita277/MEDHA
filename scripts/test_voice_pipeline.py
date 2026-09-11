import os
import sys
import tempfile
import wave
import numpy as np
import httpx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def create_synthetic_voice_wav() -> str:
    sr = 16000
    duration = 3.5  # 3.5 seconds
    t = np.linspace(0, duration, int(sr * duration))
    # Modulated audio simulating human vowel speech with breathing pauses
    f0 = 220.0
    signal = 0.4 * np.sin(2 * np.pi * f0 * t) + 0.2 * np.sin(2 * np.pi * 2 * f0 * t)
    # Modulation envelope
    envelope = (np.sin(2 * np.pi * 2.5 * t) > 0).astype(np.float32)
    audio = (signal * envelope * 0.7).astype(np.float32)

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return path

def run_test():
    print("=== Testing Voice Check-in Pipeline End-to-End ===")
    
    # 1. Login as patient (Ananya Sharma)
    client = httpx.Client(base_url="http://localhost:8000/api/v1")
    login_res = client.post("/auth/login", json={
        "email": "ananya.sharma@medha.org",
        "password": "PatientPass123!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    print("1. Patient logged in successfully. Token acquired.")

    # 2. Generate synthetic audio
    wav_path = create_synthetic_voice_wav()
    print(f"2. Synthetic WAV generated at: {wav_path} ({os.path.getsize(wav_path)} bytes)")

    try:
        # 3. Submit voice check-in (using 'current' timepoint to match active case)
        headers = {"Authorization": f"Bearer {token}"}
        with open(wav_path, "rb") as f:
            files = {"audio_file": ("test_voice_checkin.wav", f, "audio/wav")}
            data = {"timepoint": "current"}
            res = client.post("/voice/checkin", data=data, files=files, headers=headers)
        
        assert res.status_code == 200, f"Voice checkin failed: {res.status_code} - {res.text}"
        res_json = res.json()
        print("3. Voice check-in HTTP 200 OK!")
        print("   Returned Record ID:", res_json.get("id"))
        print("   Extracted Voice Score:", res_json.get("voice_score"))
        print("   Duration Seconds:", res_json.get("duration_seconds"))
        print("   Extracted Features:", res_json.get("extracted_features"))

        # 4. Verify PostgreSQL persistence
        from backend.persistence.database import SessionLocal
        from backend.persistence.models.voice_record import VoiceRecordModel
        from backend.persistence.models.prediction_result import PredictionResultModel
        from backend.persistence.models.case import Case

        db = SessionLocal()
        case = db.query(Case).filter_by(victim_id="V-LOW-001").first()
        assert case is not None, "Case V-LOW-001 not found"

        vr = db.query(VoiceRecordModel).filter_by(case_id=case.id).order_by(VoiceRecordModel.created_at.desc()).first()
        assert vr is not None, "Voice record not found in DB"
        print(f"4. DB Voice Record: duration={vr.duration_seconds}s, voice_score={vr.voice_score}")
        assert vr.voice_score is not None, "Voice score in DB is None"

        # Check prediction results for the active timepoint
        target_timepoint = case.current_timepoint or 1
        pr = db.query(PredictionResultModel).filter_by(case_id=case.id, timepoint=target_timepoint).first()
        assert pr is not None, f"Prediction result not found for timepoint {target_timepoint}"
        print(f"5. DB Unified Prediction (Timepoint {pr.timepoint}): struct={pr.structured_score}, voice={pr.voice_score}, fusion={pr.fusion_score}, triage={pr.triage_level}")
        assert pr.voice_available == True, "Voice available flag not set"
        assert pr.voice_score == vr.voice_score, "Voice score mismatch between record and prediction"

        print("=== ALL VOICE PIPELINE TESTS PASSED SUCCESSFULLY! ===")

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == "__main__":
    run_test()
