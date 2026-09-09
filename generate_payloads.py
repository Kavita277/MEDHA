import json
import numpy as np
import soundfile as sf
import os

os.makedirs("tests/payloads", exist_ok=True)

# 1. Structured
structured = {
    "Mood": 3, "Stress": 4, "Sleep": 2, "Functioning": 3, "Safety": 1,
    "Social_Support_Checkin": 1, "Self_Reported_Wellbeing": 3,
    "Threat_Event": 0, "Upcoming_Hearing": 1, "Hearing_Completed": 0,
    "Investigation_Delay": 1, "Compensation_Delay": 0, "Relocation_Stress": 1,
    "Rehabilitation_Issue": 0, "Protection_Event": 0, "Family_Support": 1,
    "Social_Support": 1, "Therapist_Engagement": 0, "Access_To_Services": 1,
    "Stable_Housing": 1, "Other_Protective_Factors": 0, "Recent_Episode": 1,
    "Episode_Severity": "Moderate", "Family_Reported_Episode": 1,
    "Case_Type": "caste_based_violence", "Case_Stage": "Investigation"
}
with open("tests/payloads/structured.json", "w") as f:
    json.dump({"data": structured}, f, indent=2)

# 2. Behaviour
behaviour = {
    "patient_id": "P001",
    "payload": {
        "day_index": 1,
        "completion_baseline_z": 0.5,
        "latency_baseline_z": 1.2,
        "question_skip_rate": 0.1,
        "session_duration_baseline_z": -0.5,
        "response_length_baseline_z": 0.0,
        "missed_checkins": 0
    }
}
with open("tests/payloads/behaviour.json", "w") as f:
    json.dump(behaviour, f, indent=2)

# 3. Temporal
temporal = {
    "features": np.random.rand(7, 72).tolist()
}
with open("tests/payloads/temporal.json", "w") as f:
    json.dump(temporal, f, indent=2)

# 4. Text
text_p = {
    "text": "I am scared to attend court."
}
with open("tests/payloads/text.json", "w") as f:
    json.dump(text_p, f, indent=2)

# 5. Voice + sample.wav
sample_rate = 22050
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
sf.write("tests/payloads/sample.wav", audio_data, sample_rate)

voice_p = {
    "audio_path": os.path.abspath("tests/payloads/sample.wav")
}
with open("tests/payloads/voice.json", "w") as f:
    json.dump(voice_p, f, indent=2)

print("Payloads and dummy audio generated.")
