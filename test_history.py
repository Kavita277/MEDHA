import requests
import time

BASE_URL = "http://127.0.0.1:8000/api"

def test_history_flow():
    print("Testing History Flow...")
    
    # 1. Create a patient
    patient_id = f"P-TEST-{int(time.time())}"
    pat_data = {
        "patient_id": patient_id,
        "name": "History Test",
        "age": 25,
        "gender": "Other",
        "phone": "999999",
        "district": "TestDist",
        "case_id": "C-TEST"
    }
    r = requests.post(f"{BASE_URL}/patients", json=pat_data)
    assert r.status_code in (200, 201), "Failed to create patient"
    
    # 2. Run Fusion (which should create Interaction & RiskHistory)
    fusion_payload = {
        "text": "I feel very sad and lonely.",
        "audio_path": "d:/Projects/SIH/tests/payloads/sample.wav",
        "patient_id": patient_id,
        "behaviour_payload": {
            "features": {
                "social_isolation": 8,
                "response_latency": 5,
                "session_skip_rate": 2,
                "duration_z_score": 3,
                "missed_sessions": 2
            }
        },
        "structured_data": {
            "Mood_Score": 2,
            "Stress_Level": 8,
            "Sleep_Quality": 2,
            "Functioning_Score": 3,
            "Safety_Score": 1,
            "Threat_Event": 1,
            "Investigation_Delay": 1,
            "Family_Support": 1
        },
        "temporal_features": [[0.1] * 72] * 7
    }
    
    print("Running fusion predict...")
    r = requests.post(f"{BASE_URL}/fusion/predict", json=fusion_payload)
    assert r.status_code == 200, "Fusion predict failed"
    fusion_data = r.json()
    assert "dds" in fusion_data
    
    # 3. Check Trend API
    r = requests.get(f"{BASE_URL}/patients/{patient_id}/trend")
    assert r.status_code == 200, "Trend API failed"
    trend_data = r.json()
    assert trend_data["current_dds"] == fusion_data["dds"]
    assert len(trend_data["last_7_predictions"]) == 1
    
    # 4. Check Timeline API
    r = requests.get(f"{BASE_URL}/patients/{patient_id}/timeline")
    assert r.status_code == 200, "Timeline API failed"
    timeline_data = r.json()
    assert "events" in timeline_data
    assert len(timeline_data["events"]) >= 2 # Should have RiskPrediction and Interaction
    
    types = [e["type"] for e in timeline_data["events"]]
    assert "RiskPrediction" in types
    assert "Interaction" in types
    
    # 5. Check History API
    r = requests.get(f"{BASE_URL}/patients/{patient_id}/history")
    assert r.status_code == 200, "History API failed"
    history_data = r.json()
    assert len(history_data["history"]) == 1
    assert history_data["history"][0]["dds"] == fusion_data["dds"]
    
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_history_flow()
