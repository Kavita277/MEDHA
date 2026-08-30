"""
MEDHA Text Engine — Integration-Ready Module
=============================================

This module wraps the EXISTING working MEDHA Text Engine inference
with a standardized JSON input/output contract.

NOTHING about the model, tokenizer, inference logic, or probability
calculation has been changed. The only addition is the thin
`medha_text_engine()` wrapper that:
  1. Accepts a standardized JSON request (dict)
  2. Extracts only the "text" field
  3. Calls the EXISTING inference (get_medha_text_features)
  4. Returns a standardized JSON response with metadata passed through

Existing functions preserved verbatim:
  - predict_medha(text)        — full inference with thresholds/predictions
  - get_medha_text_features(text) — raw 5-probability numpy vector
  - show_medha_prediction(text)   — pretty-print display
"""

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==============================================================
# 1. MODEL LOADING — EXISTING CODE (verbatim from notebook Cell 1)
# ==============================================================

FINAL_DIR = os.path.join(os.path.dirname(__file__), "Models", "medha_final_model")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(FINAL_DIR)

# Create model architecture
medha_model = AutoModelForSequenceClassification.from_pretrained(
    "google/muril-base-cased",
    num_labels=5
)

# Load your trained weights
state_dict = torch.load(
    os.path.join(FINAL_DIR, "medha_model.pt"),
    map_location=device
)

medha_model.load_state_dict(state_dict)
medha_model.to(device)
medha_model.eval()

# Load config
with open(os.path.join(FINAL_DIR, "medha_config.json"), "r") as f:
    medha_config = json.load(f)

LABELS = medha_config["labels"]
THRESHOLDS = medha_config["thresholds"]

print("Model loaded successfully.")
print("Device:", device)
print("Labels:", LABELS)
print("Thresholds:", THRESHOLDS)


# ==============================================================
# 2. EXISTING INFERENCE FUNCTIONS — UNCHANGED
# ==============================================================

def predict_medha(text):
    """
    Existing full inference function (verbatim from notebook Cell 2).
    Returns dict with probability, threshold, and prediction per label.
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    # Move tensors to GPU/CPU
    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = medha_model(**inputs)

    probabilities = torch.sigmoid(outputs.logits)[0].cpu().numpy()

    results = {}

    for i, label in enumerate(LABELS):
        threshold = THRESHOLDS[label]
        probability = float(probabilities[i])

        results[label] = {
            "probability": probability,
            "threshold": threshold,
            "prediction": int(probability >= threshold)
        }

    return results


def get_medha_text_features(text):
    """
    Existing vector inference function (verbatim from notebook Cell 9).
    Returns raw numpy array of 5 probabilities.
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = medha_model(**inputs)

    probabilities = torch.sigmoid(outputs.logits)[0].cpu().numpy()

    return probabilities


def show_medha_prediction(text):
    """
    Existing display function (verbatim from notebook Cell 3).
    Pretty-prints inference results.
    """
    results = predict_medha(text)

    print("=" * 70)
    print("MEDHA PREDICTION")
    print("=" * 70)

    print("\nTEXT:")
    print(text)

    print("\nRESULTS:")
    print("-" * 70)

    for label, result in results.items():

        status = "YES" if result["prediction"] == 1 else "NO"

        print(
            f"{label:<25} "
            f"Probability: {result['probability']:.3f} | "
            f"Threshold: {result['threshold']:.2f} | "
            f"Prediction: {status}"
        )

    print("=" * 70)


# ==============================================================
# 3. INTEGRATION WRAPPER — NEW (thin layer only)
# ==============================================================

# Mapping from internal model label names to the standardized
# text_vector field names required by the MEDHA integration contract.
_LABEL_TO_VECTOR_KEY = {
    "Distress_Label": "text_distress",
    "Fear_Label": "fear_signal",
    "Threat_Label": "threat_context",
    "Negative_Affect_Label": "negative_affect",
    "Urgency_Label": "urgency",
}

# Valid source values (for documentation; not enforced to avoid
# brittleness if new sources are added later).
VALID_SOURCES = {"question_engine", "diary", "chatbot", "voice_transcript"}

# Valid language values (metadata only — NOT passed to model).
VALID_LANGUAGES = {"en", "hi", "hinglish"}


def medha_text_engine(request: dict) -> dict:
    """
    Integration wrapper for the MEDHA Text Engine.

    Accepts a standardized JSON request dict and returns a standardized
    JSON response dict. The ONLY field that touches the ML model is
    request["text"] — all other fields are metadata passed through
    unchanged.

    Parameters
    ----------
    request : dict
        {
            "victim_id": str,
            "session_id": str,
            "timestamp": str (ISO-8601),
            "text": str,           # ONLY this goes to MuRIL
            "language": str,       # metadata only (optional)
            "source": str          # metadata only
        }

    Returns
    -------
    dict
        {
            "victim_id": ...,
            "session_id": ...,
            "timestamp": ...,
            "language": ...,
            "source": ...,
            "text_available": 1,
            "text_vector": {
                "text_distress": float,
                "fear_signal": float,
                "threat_context": float,
                "negative_affect": float,
                "urgency": float
            }
        }

    Raises
    ------
    ValueError
        If "text" is missing, empty, or whitespace-only.
    TypeError
        If request is not a dict.
    """
    # --- Input validation ---
    if not isinstance(request, dict):
        raise TypeError(
            f"Request must be a dict, got {type(request).__name__}"
        )

    text = request.get("text")

    if text is None or not str(text).strip():
        raise ValueError(
            "Text is required and cannot be empty. "
            "Do not call the Text Engine without actual text content."
        )

    # --- Call EXISTING inference (unchanged) ---
    probabilities = get_medha_text_features(str(text).strip())

    # --- Build text_vector from existing probabilities ---
    text_vector = {}
    for i, label in enumerate(LABELS):
        vector_key = _LABEL_TO_VECTOR_KEY[label]
        text_vector[vector_key] = round(float(probabilities[i]), 6)

    # --- Return standardized output with metadata passed through ---
    return {
        "victim_id": request.get("victim_id"),
        "session_id": request.get("session_id"),
        "timestamp": request.get("timestamp"),
        "language": request.get("language"),       # safe if absent → None
        "source": request.get("source"),
        "text_available": 1,
        "text_vector": text_vector,
    }
