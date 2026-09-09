"""
MEDHA Chatbot LLM Module
=========================
Provider-independent LLM abstraction for conversational response generation
and semantic observation extraction.

Exports:
- GeminiProvider: Production provider using Google Gemini API.
- MockLLMProvider: Deterministic provider for offline/unit testing.
- CANDIDATE_OBSERVATION_DOMAINS: Controlled vocabulary for observation extraction.
"""

from .gemini_provider import GeminiProvider
from .mock_provider import MockLLMProvider
from .observation_schema import CANDIDATE_OBSERVATION_DOMAINS

__all__ = [
    "GeminiProvider",
    "MockLLMProvider",
    "CANDIDATE_OBSERVATION_DOMAINS",
]
