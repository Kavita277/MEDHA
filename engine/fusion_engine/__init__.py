"""
MEDHA Weighted Fusion Engine
=============================

Combines specialist engine outputs (Text, Voice, Behaviour, Structured,
Temporal) into a single fused risk score and Dynamic Distress Score (DDS).

This module does NOT modify any existing engine. It only consumes their
outputs through thin adapters.
"""

from .fusion import compute_fusion
from .adapters import (
    adapt_text_output,
    adapt_voice_output,
    adapt_behaviour_output,
    adapt_structured_output,
    adapt_temporal_output,
)
from .weights import FUSION_WEIGHTS
from .schemas import FusionInput, ModalitySignal, FusionOutput

__all__ = [
    "compute_fusion",
    "adapt_text_output",
    "adapt_voice_output",
    "adapt_behaviour_output",
    "adapt_structured_output",
    "adapt_temporal_output",
    "FUSION_WEIGHTS",
    "FusionInput",
    "ModalitySignal",
    "FusionOutput",
]
