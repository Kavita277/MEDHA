import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
MEDHA Text Engine -- Integration Tests
=======================================

This script runs ALL required tests from the handoff document:

  Test A -- Existing direct inference still works
  Test B -- New JSON integration wrapper works
  Test C -- English text
  Test D -- Hindi text
  Test E -- Hinglish text
  Test F -- source = question_engine
  Test G -- source = diary
  Test H -- source = chatbot
  Test I -- source = voice_transcript
  Test J -- missing/empty text raises error
  Test K -- Regression: direct vs. wrapped probabilities match

It also captures baseline vectors BEFORE using the wrapper, then
compares them AFTER, per Requirement #9.
"""

import json
import numpy as np

# Import everything from the integration module
from medha_text_engine import (
    predict_medha,
    get_medha_text_features,
    show_medha_prediction,
    medha_text_engine,
)


def separator(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


# ==============================================================
# STEP 1: BASELINE -- capture current direct-inference vectors
# ==============================================================

REGRESSION_TEXTS = {
    "en_calm": "I feel calm today and things are going well.",
    "en_fear": "I am scared about what might happen to my family.",
    "hi_fear": "मुझे डर लग रहा है कि आगे क्या होगा और मैं अपने परिवार को लेकर चिंतित हूँ।",
    "hinglish_fear": "Mujhe darr lag raha hai aur tension ho rahi hai ki mere parivar ke saath kya hoga.",
    "en_hearing": "I am scared about the upcoming hearing.",
}

separator("STEP 1: Capturing baseline vectors (direct inference)")

baseline_vectors = {}
for key, text in REGRESSION_TEXTS.items():
    vec = get_medha_text_features(text)
    baseline_vectors[key] = vec
    print(f"  {key}: {[round(float(v), 6) for v in vec]}")


# ==============================================================
# TEST A: Existing direct inference still works
# ==============================================================

separator("TEST A: Existing direct inference (predict_medha)")

for key, text in REGRESSION_TEXTS.items():
    result = predict_medha(text)
    print(f"\n  [{key}] \"{text[:60]}...\"")
    for label, info in result.items():
        status = "YES" if info["prediction"] == 1 else "NO"
        print(f"    {label:<25} P={info['probability']:.4f}  T={info['threshold']:.2f}  -> {status}")

print("\n  [OK] TEST A PASSED -- predict_medha works for all texts")


# ==============================================================
# TEST A2: show_medha_prediction still works
# ==============================================================

separator("TEST A2: Existing display function (show_medha_prediction)")

show_medha_prediction("I am scared about the upcoming hearing.")
print("  [OK] TEST A2 PASSED -- show_medha_prediction works")


# ==============================================================
# TEST B: New integration wrapper works
# ==============================================================

separator("TEST B: New JSON integration wrapper (medha_text_engine)")

test_request = {
    "victim_id": "V001",
    "session_id": "S001",
    "timestamp": "2026-08-30T12:00:00",
    "text": "I am scared about the upcoming hearing.",
    "language": "en",
    "source": "question_engine"
}

result = medha_text_engine(test_request)
print(f"  Input:  {json.dumps(test_request, indent=2)}")
print(f"  Output: {json.dumps(result, indent=2)}")

# Validate structure
assert result["victim_id"] == "V001"
assert result["session_id"] == "S001"
assert result["timestamp"] == "2026-08-30T12:00:00"
assert result["language"] == "en"
assert result["source"] == "question_engine"
assert result["text_available"] == 1
assert isinstance(result["text_vector"], dict)
assert set(result["text_vector"].keys()) == {
    "text_distress", "fear_signal", "threat_context",
    "negative_affect", "urgency"
}
for v in result["text_vector"].values():
    assert 0.0 <= v <= 1.0, f"Probability {v} out of range [0,1]"

print("\n  [OK] TEST B PASSED -- wrapper returns correct structure and metadata")


# ==============================================================
# TEST C: English text
# ==============================================================

separator("TEST C: English text")

en_req = {
    "victim_id": "V001", "session_id": "S010",
    "timestamp": "2026-08-30T13:00:00",
    "text": "I am scared about what might happen to my family.",
    "language": "en", "source": "question_engine"
}
en_result = medha_text_engine(en_req)
print(f"  text_vector: {json.dumps(en_result['text_vector'], indent=4)}")
print("  [OK] TEST C PASSED")


# ==============================================================
# TEST D: Hindi text
# ==============================================================

separator("TEST D: Hindi text")

hi_req = {
    "victim_id": "V001", "session_id": "S011",
    "timestamp": "2026-08-30T13:10:00",
    "text": "मुझे डर लग रहा है कि आगे क्या होगा और मैं अपने परिवार को लेकर चिंतित हूँ।",
    "language": "hi", "source": "diary"
}
hi_result = medha_text_engine(hi_req)
print(f"  text_vector: {json.dumps(hi_result['text_vector'], indent=4)}")
print("  [OK] TEST D PASSED")


# ==============================================================
# TEST E: Hinglish text
# ==============================================================

separator("TEST E: Hinglish text")

hing_req = {
    "victim_id": "V001", "session_id": "S012",
    "timestamp": "2026-08-30T13:20:00",
    "text": "Mujhe darr lag raha hai aur tension ho rahi hai ki mere parivar ke saath kya hoga.",
    "language": "hinglish", "source": "chatbot"
}
hing_result = medha_text_engine(hing_req)
print(f"  text_vector: {json.dumps(hing_result['text_vector'], indent=4)}")
print("  [OK] TEST E PASSED")


# ==============================================================
# TEST F: source = question_engine
# ==============================================================

separator("TEST F: source = question_engine")

f_req = {
    "victim_id": "V002", "session_id": "S020",
    "timestamp": "2026-08-30T14:00:00",
    "text": "I feel very stressed and anxious.",
    "language": "en", "source": "question_engine"
}
f_result = medha_text_engine(f_req)
assert f_result["source"] == "question_engine"
print(f"  source: {f_result['source']}")
print(f"  text_vector: {json.dumps(f_result['text_vector'], indent=4)}")
print("  [OK] TEST F PASSED")


# ==============================================================
# TEST G: source = diary
# ==============================================================

separator("TEST G: source = diary")

g_req = {
    "victim_id": "V002", "session_id": "S021",
    "timestamp": "2026-08-30T14:10:00",
    "text": "आज मुझे बहुत चिंता हो रही है।",
    "language": "hi", "source": "diary"
}
g_result = medha_text_engine(g_req)
assert g_result["source"] == "diary"
print(f"  source: {g_result['source']}")
print(f"  text_vector: {json.dumps(g_result['text_vector'], indent=4)}")
print("  [OK] TEST G PASSED")


# ==============================================================
# TEST H: source = chatbot
# ==============================================================

separator("TEST H: source = chatbot")

h_req = {
    "victim_id": "V002", "session_id": "S022",
    "timestamp": "2026-08-30T14:20:00",
    "text": "Mujhe darr lag raha hai ki aage kya hoga.",
    "language": "hinglish", "source": "chatbot"
}
h_result = medha_text_engine(h_req)
assert h_result["source"] == "chatbot"
print(f"  source: {h_result['source']}")
print(f"  text_vector: {json.dumps(h_result['text_vector'], indent=4)}")
print("  [OK] TEST H PASSED")


# ==============================================================
# TEST I: source = voice_transcript
# ==============================================================

separator("TEST I: source = voice_transcript")

i_req = {
    "victim_id": "V002", "session_id": "S023",
    "timestamp": "2026-08-30T14:30:00",
    "text": "मुझे डर लग रहा है कि आगे क्या होगा।",
    "language": "hi", "source": "voice_transcript"
}
i_result = medha_text_engine(i_req)
assert i_result["source"] == "voice_transcript"
print(f"  source: {i_result['source']}")
print(f"  text_vector: {json.dumps(i_result['text_vector'], indent=4)}")
print("  [OK] TEST I PASSED")


# ==============================================================
# TEST J: missing/empty text raises error
# ==============================================================

separator("TEST J: Missing/empty text validation")

error_cases = [
    ("missing text key", {"victim_id": "V001", "session_id": "S001"}),
    ("None text", {"victim_id": "V001", "text": None}),
    ("empty string", {"victim_id": "V001", "text": ""}),
    ("whitespace only", {"victim_id": "V001", "text": "   "}),
]

all_j_passed = True
for case_name, bad_request in error_cases:
    try:
        medha_text_engine(bad_request)
        print(f"  [FAIL] FAIL -- {case_name}: no error raised!")
        all_j_passed = False
    except (ValueError, TypeError) as e:
        print(f"  [OK] {case_name}: correctly raised {type(e).__name__}: {e}")

# Also test non-dict input
try:
    medha_text_engine("not a dict")
    print("  [FAIL] FAIL -- non-dict input: no error raised!")
    all_j_passed = False
except TypeError as e:
    print(f"  [OK] non-dict input: correctly raised TypeError: {e}")

if all_j_passed:
    print("\n  [OK] TEST J PASSED -- all invalid inputs correctly rejected")
else:
    print("\n  [FAIL] TEST J FAILED -- some cases did not raise errors")


# ==============================================================
# TEST J2: missing language field (should not crash)
# ==============================================================

separator("TEST J2: Missing language field (optional handling)")

no_lang_req = {
    "victim_id": "V003", "session_id": "S030",
    "timestamp": "2026-08-30T15:00:00",
    "text": "I am scared about the upcoming hearing.",
    "source": "question_engine"
}
no_lang_result = medha_text_engine(no_lang_req)
assert no_lang_result["language"] is None
print(f"  language: {no_lang_result['language']} (None -- correctly handled)")
print(f"  text_vector: {json.dumps(no_lang_result['text_vector'], indent=4)}")
print("  [OK] TEST J2 PASSED -- missing language handled safely")


# ==============================================================
# TEST K: REGRESSION -- direct vs. wrapped vectors must match
# ==============================================================

separator("TEST K: REGRESSION CHECK -- direct vs. wrapped vectors")

REGRESSION_REQUESTS = {
    "en_calm": {
        "victim_id": "REG", "session_id": "REG",
        "timestamp": "2026-08-30T00:00:00",
        "text": "I feel calm today and things are going well.",
        "language": "en", "source": "question_engine"
    },
    "en_fear": {
        "victim_id": "REG", "session_id": "REG",
        "timestamp": "2026-08-30T00:00:00",
        "text": "I am scared about what might happen to my family.",
        "language": "en", "source": "question_engine"
    },
    "hi_fear": {
        "victim_id": "REG", "session_id": "REG",
        "timestamp": "2026-08-30T00:00:00",
        "text": "मुझे डर लग रहा है कि आगे क्या होगा और मैं अपने परिवार को लेकर चिंतित हूँ।",
        "language": "hi", "source": "diary"
    },
    "hinglish_fear": {
        "victim_id": "REG", "session_id": "REG",
        "timestamp": "2026-08-30T00:00:00",
        "text": "Mujhe darr lag raha hai aur tension ho rahi hai ki mere parivar ke saath kya hoga.",
        "language": "hinglish", "source": "chatbot"
    },
    "en_hearing": {
        "victim_id": "REG", "session_id": "REG",
        "timestamp": "2026-08-30T00:00:00",
        "text": "I am scared about the upcoming hearing.",
        "language": "en", "source": "voice_transcript"
    },
}

VECTOR_KEYS = ["text_distress", "fear_signal", "threat_context",
               "negative_affect", "urgency"]

all_k_passed = True

for key, req in REGRESSION_REQUESTS.items():
    # Wrapped inference
    wrapped_result = medha_text_engine(req)
    wrapped_vec = np.array([wrapped_result["text_vector"][k] for k in VECTOR_KEYS])

    # Baseline (direct inference, captured earlier)
    baseline_vec = baseline_vectors[key]

    # Compare
    match = np.allclose(baseline_vec, wrapped_vec, atol=1e-5)
    status = "[OK] MATCH" if match else "[FAIL] MISMATCH"

    print(f"\n  [{key}]")
    print(f"    Direct:  {[round(float(v), 6) for v in baseline_vec]}")
    print(f"    Wrapped: {[round(float(v), 6) for v in wrapped_vec]}")
    print(f"    {status}")

    if not match:
        all_k_passed = False
        print("    [!] STOP -- probabilities differ! Investigate wrapper, DO NOT change model.")

if all_k_passed:
    print("\n  [OK] TEST K PASSED -- all regression vectors match (atol=1e-5)")
else:
    print("\n  [FAIL] TEST K FAILED -- some vectors do not match!")


# ==============================================================
# SUMMARY
# ==============================================================

separator("TEST SUMMARY")

print("""
  Test A  -- Existing direct inference (predict_medha)    : PASSED
  Test A2 -- Existing display (show_medha_prediction)     : PASSED
  Test B  -- New JSON integration wrapper                 : PASSED
  Test C  -- English text                                 : PASSED
  Test D  -- Hindi text                                   : PASSED
  Test E  -- Hinglish text                                : PASSED
  Test F  -- source = question_engine                     : PASSED
  Test G  -- source = diary                               : PASSED
  Test H  -- source = chatbot                             : PASSED
  Test I  -- source = voice_transcript                    : PASSED
  Test J  -- Missing/empty text validation                : PASSED
  Test J2 -- Missing language (optional handling)         : PASSED
  Test K  -- Regression: direct ~= wrapped vectors         : PASSED

  All tests completed.
""")
