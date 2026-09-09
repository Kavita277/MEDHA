"""
MEDHA Chatbot Package
=====================
Orchestration and conversational interface layer around the frozen MEDHA V2 predictive pipeline.
"""

__version__ = "2.0.0"

from .conversation_manager import ConversationManager, ConversationSession, TurnResult
from .state.medha_state import MedhaState
from .v2_adapter.medha_v2_adapter import MedhaV2Adapter
from .engines.text_adapter import MedhaTextAdapter

__all__ = [
    "ConversationManager",
    "ConversationSession",
    "TurnResult",
    "MedhaState",
    "MedhaV2Adapter",
    "MedhaTextAdapter",
]
