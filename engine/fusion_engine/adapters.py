"""
MEDHA Fusion Engine — Adapters
================================

Thin translation layer that converts each existing engine's raw output
into the standardised ``ModalitySignal(available, risk)`` pair consumed
by the fusion formula.

IMPORTANT
---------
* These functions do NOT call the engines.  They only reshape/aggregate
  the dict that an engine *already returned*.
* No existing engine code is imported or modified.
* Each adapter documents exactly which fields it reads.
"""

try:
    from .schemas import ModalitySignal
except ImportError:
    from schemas import ModalitySignal



# ================================================================
# TEXT ENGINE ADAPTER
# ================================================================

def adapt_text_output(text_engine_output: dict) -> ModalitySignal:
    """
    Convert the existing Text Engine JSON into a single text_risk.

    Expected input keys (from ``medha_text_engine()``):
        text_available : int (1 or 0)
        text_vector : {
            text_distress    : float 0–1,
            fear_signal      : float 0–1,
            threat_context   : float 0–1,
            negative_affect  : float 0–1,
            urgency          : float 0–1,
        }

    Aggregation:
        text_risk = mean(text_distress, fear_signal, threat_context,
                         negative_affect, urgency)
    """
    if not text_engine_output:
        return ModalitySignal(available=False)

    available = bool(text_engine_output.get("text_available", 0))

    if not available:
        return ModalitySignal(available=False)

    vec = text_engine_output.get("text_vector", {})

    values = [
        vec.get("text_distress"),
        vec.get("fear_signal"),
        vec.get("threat_context"),
        vec.get("negative_affect"),
        vec.get("urgency"),
    ]

    # If any sub-signal is missing, we cannot produce a reliable
    # aggregate — mark as unavailable rather than silently dropping.
    if any(v is None for v in values):
        return ModalitySignal(available=False)

    text_risk = sum(values) / len(values)

    return ModalitySignal(available=True, risk=text_risk)


# ================================================================
# VOICE ENGINE ADAPTER
# ================================================================

def adapt_voice_output(voice_engine_output: dict) -> ModalitySignal:
    """
    Convert the existing Voice Engine JSON into a single voice_risk.

    Expected input keys (from ``/analyze-voice`` response):
        voice_available : bool
        fusion_features : {
            voice_available  : int (1 or 0),
            voice_distress   : float 0–1,
            ...              : (other fields preserved but unused here)
        }

    Aggregation:
        voice_risk = voice_distress

    voice_confidence is NOT used as a risk value (per spec).
    """
    if not voice_engine_output:
        return ModalitySignal(available=False)

    available = voice_engine_output.get("voice_available", False)

    if not available:
        return ModalitySignal(available=False)

    fusion = voice_engine_output.get("fusion_features", {})
    voice_distress = fusion.get("voice_distress")

    if voice_distress is None:
        return ModalitySignal(available=False)

    return ModalitySignal(available=True, risk=float(voice_distress))


# ================================================================
# BEHAVIOUR ENGINE ADAPTER
# ================================================================

def adapt_behaviour_output(behaviour_engine_output: dict) -> ModalitySignal:
    """
    Convert the existing Behaviour Engine JSON into a single
    behaviour_risk.

    Expected input keys (from ``/v1/patients/{id}/score``):
        anomaly_score         : float 0–1 (percentile-ranked)
        engagement_deviation  : float ≥ 0 (mean abs z-scores)
        inactivity_score      : float ≥ 0 (rolling mean missed)

    Aggregation (matches the engine's own internal formula, lines 105-106
    of medha_scoring_api.py):
        behaviour_risk = 0.40 * anomaly_score
                       + 0.30 * clip(engagement_deviation / 3.0, 0, 1)
                       + 0.30 * clip(inactivity_score, 0, 1)
    """
    if not behaviour_engine_output:
        return ModalitySignal(available=False)

    anomaly = behaviour_engine_output.get("anomaly_score")
    engagement = behaviour_engine_output.get("engagement_deviation")
    inactivity = behaviour_engine_output.get("inactivity_score")

    # If the engine flagged insufficient history, anomaly_score is None
    if anomaly is None:
        return ModalitySignal(available=False)

    # Normalise engagement_deviation the same way the engine does
    eng_norm = min(max((engagement or 0.0) / 3.0, 0.0), 1.0)
    inact_norm = min(max(inactivity or 0.0, 0.0), 1.0)

    behaviour_risk = (
        0.40 * float(anomaly)
        + 0.30 * eng_norm
        + 0.30 * inact_norm
    )

    return ModalitySignal(available=True, risk=behaviour_risk)


# ================================================================
# STRUCTURED / XGBOOST ENGINE ADAPTER
# ================================================================

def adapt_structured_output(structured_engine_output: dict) -> ModalitySignal:
    """
    Convert the existing Structured Engine JSON into a single
    structured_risk.

    Expected input keys (from ``structured_risk_with_explanation()``
    or ``structured_risk_inference()``):
        structured_available : bool
        structured_risk      : float 0–1 (probability)

    Aggregation:
        structured_risk = structured_risk  (passthrough)
    """
    if not structured_engine_output:
        return ModalitySignal(available=False)

    available = structured_engine_output.get("structured_available", False)

    if not available:
        return ModalitySignal(available=False)

    risk = structured_engine_output.get("structured_risk")

    if risk is None:
        return ModalitySignal(available=False)

    return ModalitySignal(available=True, risk=float(risk))


# ================================================================
# GRU / TEMPORAL ENGINE ADAPTER
# ================================================================

def adapt_temporal_output(temporal_engine_output: dict) -> ModalitySignal:
    """
    Convert the existing GRU Engine JSON into a single temporal_risk.

    Expected input keys (from ``/predict``):
        temporal_risk_score : float 0–1 (calibrated probability)
        prediction          : int   (NOT used)
        threshold_used      : float (NOT used)

    Aggregation:
        temporal_risk = temporal_risk_score  (passthrough)
    """
    if not temporal_engine_output:
        return ModalitySignal(available=False)

    risk = temporal_engine_output.get("temporal_risk_score")

    if risk is None:
        return ModalitySignal(available=False)

    return ModalitySignal(available=True, risk=float(risk))
