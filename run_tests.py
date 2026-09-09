import json
import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

log_entries = []

def log_result(engine, endpoint, status, proc_time, msg):
    timestamp = datetime.now().isoformat()
    log = f"[{timestamp}] Engine: {engine} | Endpoint: {endpoint} | Status: {status} | Time: {proc_time:.2f}ms | {msg}"
    print(log)
    log_entries.append(log)

# Test Health
def test_health():
    for eng in ["text", "voice", "behaviour", "structured", "temporal"]:
        url = f"{BASE_URL}/health/{eng}"
        try:
            r = requests.get(url)
            log_result(eng.upper(), f"/health/{eng}", r.status_code, r.elapsed.total_seconds()*1000, r.text)
        except Exception as e:
            log_result(eng.upper(), f"/health/{eng}", "ERROR", 0, str(e))

def test_inference():
    endpoints = [
        ("TEXT", "/analyze/text", "tests/payloads/text.json"),
        ("VOICE", "/analyze/voice", "tests/payloads/voice.json"),
        ("BEHAVIOUR", "/analyze/behaviour", "tests/payloads/behaviour.json"),
        ("STRUCTURED", "/risk/structured", "tests/payloads/structured.json"),
        ("TEMPORAL", "/predict", "tests/payloads/temporal.json")
    ]
    for eng, ep, payload_file in endpoints:
        url = f"{BASE_URL}{ep}"
        try:
            with open(payload_file, "r") as f:
                payload = json.load(f)
            
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                data = r.json()
                engine_time = data.get("processing_time_ms", 0.0)
                log_result(eng, ep, r.status_code, engine_time, "SUCCESS")
            else:
                log_result(eng, ep, r.status_code, r.elapsed.total_seconds()*1000, r.text)
        except Exception as e:
            log_result(eng, ep, "ERROR", 0, str(e))

if __name__ == "__main__":
    print("--- Running Health Checks ---")
    test_health()
    print("\n--- Running Inference Tests ---")
    test_inference()
    
    with open("tests/validation_report.txt", "w") as f:
        f.write("\n".join(log_entries))
