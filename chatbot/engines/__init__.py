"""
MEDHA Chatbot Engines Module
============================
Adapters for existing specialist engines (Text, Voice, Behaviour).
"""

from .text_adapter import MedhaTextAdapter, TextEngineResult

__all__ = [
    "MedhaTextAdapter",
    "TextEngineResult",
]
