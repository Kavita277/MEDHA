"""
MEDHA Fusion Engine — Data Schemas
====================================

Plain dataclasses describing the fusion input and output contracts.
No framework dependency (no Pydantic required at this layer).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ModalitySignal:
    """One specialist engine's contribution to fusion."""

    available: bool
    risk: Optional[float] = None  # 0–1 when available, None when not


@dataclass
class FusionInput:
    """
    Everything the fusion engine needs for one observation.

    Fields
    ------
    patient_id : str
        Passed through unchanged.
    timestamp : str
        ISO-8601 timestamp, passed through unchanged.
    text, voice, behaviour, structured, temporal : ModalitySignal
        Each carries an ``available`` flag and a ``risk`` value.
    """

    patient_id: str
    timestamp: str

    text: ModalitySignal = field(default_factory=lambda: ModalitySignal(available=False))
    voice: ModalitySignal = field(default_factory=lambda: ModalitySignal(available=False))
    behaviour: ModalitySignal = field(default_factory=lambda: ModalitySignal(available=False))
    structured: ModalitySignal = field(default_factory=lambda: ModalitySignal(available=False))
    temporal: ModalitySignal = field(default_factory=lambda: ModalitySignal(available=False))


@dataclass
class FusionOutput:
    """
    Complete fusion result for one observation.

    Fields
    ------
    patient_id, timestamp : str
        Passed through from input.
    fusion_available : bool
        False only when every modality is unavailable.
    signals : dict
        Per-modality risk values actually used.
    availability : dict
        Per-modality availability flags (1/0).
    effective_weights : dict
        Weights after redistribution for missing modalities.
    fused_risk : float or None
        Weighted combination of available risks (0–1).
    dds : float or None
        Dynamic Distress Score = fused_risk × 100 (0–100).
    future_escalation : dict or str
        Future escalation risk from the GRU (7-day window) or 'not_available'.
    """

    patient_id: str
    timestamp: str

    fusion_available: bool

    signals: Dict[str, Optional[float]]
    availability: Dict[str, int]
    effective_weights: Dict[str, float]

    fused_risk: Optional[float]
    dds: Optional[float]
    future_escalation: dict | str = "not_available"

    def to_dict(self) -> dict:
        """Serialise to a plain dict (JSON-safe)."""
        return {
            "patient_id": self.patient_id,
            "timestamp": self.timestamp,
            "fusion_available": self.fusion_available,
            "signals": self.signals,
            "availability": self.availability,
            "effective_weights": self.effective_weights,
            "fused_risk": self.fused_risk,
            "dds": self.dds,
            "future_escalation": self.future_escalation,
        }
