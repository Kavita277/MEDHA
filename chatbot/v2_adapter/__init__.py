"""
MEDHA Chatbot V2 Adapter Module
===============================
Thin integration adapter connecting chatbot MedhaState to the frozen MEDHA V2 predictive pipeline.
"""

from .medha_v2_adapter import MedhaV2Adapter, V2PredictionResult

__all__ = [
    "MedhaV2Adapter",
    "V2PredictionResult",
]
