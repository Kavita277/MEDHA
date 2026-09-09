import json
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api"

# Construct a master payload
fusion_payload = {}
with open("tests/payloads/text.json", "r") as f:
    fusion_payload["text"] = json.load(f)["text"]

with open("tests/payloads/voice.json", "r") as f:
    fusion_payload["audio_path"] = json.load(f)["audio_path"]

with open("tests/payloads/behaviour.json", "r") as f:
    b = json.load(f)
    fusion_payload["patient_id"] = b["patient_id"]
    fusion_payload["behaviour_payload"] = b["payload"]

with open("tests/payloads/structured.json", "r") as f:
    fusion_payload["structured_data"] = json.load(f)["data"]

with open("tests/payloads/temporal.json", "r") as f:
    fusion_payload["temporal_features"] = json.load(f)["features"]

print("Testing /fusion/predict...")
try:
    r = requests.post(f"{BASE_URL}/fusion/predict", json=fusion_payload)
    print("Status Code:", r.status_code)
    print("Response JSON:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print("Error:", e)
