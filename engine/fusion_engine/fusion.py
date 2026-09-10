"""
MEDHA Fusion Engine — Weighted Fusion
=======================================

Core fusion logic.  Takes a ``FusionInput`` (five ModalitySignal
values) and produces a ``FusionOutput`` containing the fused risk,
DDS, effective weights, and full metadata.

Formula (all modalities available)
----------------------------------
    fused_risk = 0.25 * text_risk
               + 0.15 * voice_risk
               + 0.15 * behaviour_risk
               + 0.25 * structured_risk
               + 0.20 * temporal_risk

    DDS = fused_risk × 100

Missing-modality handling
-------------------------
If a modality is unavailable, its weight is redistributed
proportionally among the remaining modalities so that effective
weights always sum to 1.0.

If ALL modalities are unavailable, ``fusion_available=False`` and
both ``fused_risk`` and ``dds`` are ``None``.
"""

try:
    from .schemas import FusionInput, FusionOutput, ModalitySignal
    from .weights import FUSION_WEIGHTS
except ImportError:
    from schemas import FusionInput, FusionOutput, ModalitySignal
    from weights import FUSION_WEIGHTS



# Ordered list of modality keys — must match FusionInput field names
# and FUSION_WEIGHTS keys.
_MODALITY_KEYS = ["text", "voice", "behaviour", "structured", "temporal"]


def compute_fusion(fusion_input: FusionInput) -> FusionOutput:
    """
    Run the weighted fusion on the given specialist signals.

    Parameters
    ----------
    fusion_input : FusionInput
        Populated with ModalitySignal values for each engine.

    Returns
    -------
    FusionOutput
        Fused risk, DDS, effective weights, and metadata.
    """

    # ------------------------------------------------------------------
    # 1. Collect availability + risk for each modality
    # ------------------------------------------------------------------
    signals: dict[str, ModalitySignal] = {
        "text":       fusion_input.text,
        "voice":      fusion_input.voice,
        "behaviour":  fusion_input.behaviour,
        "structured": fusion_input.structured,
        "temporal":   fusion_input.temporal,
    }

    availability = {
        key: int(sig.available)
        for key, sig in signals.items()
    }

    signal_values = {
        key: sig.risk if sig.available else None
        for key, sig in signals.items()
    }

    # ------------------------------------------------------------------
    # 2. Determine available modalities
    # ------------------------------------------------------------------
    available_keys = [
        key for key in _MODALITY_KEYS
        if signals[key].available and signals[key].risk is not None
    ]

    # ------------------------------------------------------------------
    # 3. Edge case: nothing available
    # ------------------------------------------------------------------
    if not available_keys:
        return FusionOutput(
            patient_id=fusion_input.patient_id,
            timestamp=fusion_input.timestamp,
            fusion_available=False,
            signals=signal_values,
            availability=availability,
            effective_weights={key: 0.0 for key in _MODALITY_KEYS},
            fused_risk=None,
            dds=None,
        )

    # ------------------------------------------------------------------
    # 4. Renormalise weights for available modalities
    # ------------------------------------------------------------------
    raw_weight_sum = sum(
        FUSION_WEIGHTS[key] for key in available_keys
    )

    effective_weights = {}
    for key in _MODALITY_KEYS:
        if key in available_keys:
            effective_weights[key] = FUSION_WEIGHTS[key] / raw_weight_sum
        else:
            effective_weights[key] = 0.0

    # ------------------------------------------------------------------
    # 5. Weighted sum
    # ------------------------------------------------------------------
    fused_risk = sum(
        effective_weights[key] * signals[key].risk
        for key in available_keys
    )

    # Clamp to [0, 1] for safety (should already be in range if
    # individual risks are 0–1, but defensive).
    fused_risk = max(0.0, min(1.0, fused_risk))

    # ------------------------------------------------------------------
    # 6. DDS
    # ------------------------------------------------------------------
    dds = round(fused_risk * 100, 2)

    # ------------------------------------------------------------------
    # 7. Future Escalation
    # ------------------------------------------------------------------
    if fusion_input.temporal.available and fusion_input.temporal.risk is not None:
        future_escalation = {
            "risk": round(fusion_input.temporal.risk, 6),
            "window_days": 7,
            "prediction": int(fusion_input.temporal.risk >= 0.15)
        }
    else:
        future_escalation = "not_available"

    return FusionOutput(
        patient_id=fusion_input.patient_id,
        timestamp=fusion_input.timestamp,
        fusion_available=True,
        signals=signal_values,
        availability=availability,
        effective_weights={
            key: round(w, 6) for key, w in effective_weights.items()
        },
        fused_risk=round(fused_risk, 6),
        dds=dds,
        future_escalation=future_escalation,
    )
