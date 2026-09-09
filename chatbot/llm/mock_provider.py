"""
Mock LLM Provider
==================

Deterministic, offline LLM provider for unit testing and CI environments.

Produces predictable responses and optionally extracts rule-based
candidate observations from user messages using keyword matching.
No API calls. No secrets required.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from chatbot.interfaces import LLMResponse
from chatbot.state.medha_state import MedhaState, QuestionRecord
from chatbot.llm.observation_schema import CANDIDATE_OBSERVATION_DOMAINS


# Simple keyword → observation rules for deterministic testing
_KEYWORD_RULES: List[Dict[str, Any]] = [
    {
        "pattern": re.compile(r"(?:can'?t|couldn'?t|barely|haven'?t|not)\s+(?:sleep|slept|sleeping)", re.IGNORECASE),
        "domain": "sleep",
        "value": "poor",
        "confidence": 0.90,
    },
    {
        "pattern": re.compile(r"(?:scared|afraid|frightened|terrified|fear)", re.IGNORECASE),
        "domain": "fear",
        "value": "present",
        "confidence": 0.88,
    },
    {
        "pattern": re.compile(r"(?:stressed|overwhelmed|pressure|burning\s*out|overloaded)", re.IGNORECASE),
        "domain": "stress",
        "value": "high",
        "confidence": 0.85,
    },
    {
        "pattern": re.compile(r"(?:sad|depressed|down|hopeless|miserable|unhappy|low\s*mood)", re.IGNORECASE),
        "domain": "mood",
        "value": "low",
        "confidence": 0.87,
    },
    {
        "pattern": re.compile(r"(?:alone|isolated|no\s*one|nobody|don'?t\s+talk)", re.IGNORECASE),
        "domain": "social_support",
        "value": "reduced",
        "confidence": 0.84,
    },
    {
        "pattern": re.compile(r"(?:unsafe|danger|threatened|not\s+safe|in\s+danger)", re.IGNORECASE),
        "domain": "safety",
        "value": "unsafe",
        "confidence": 0.92,
    },
    {
        "pattern": re.compile(r"(?:urgent|emergency|immediately|right\s+now|can'?t\s+wait)", re.IGNORECASE),
        "domain": "urgency",
        "value": "high",
        "confidence": 0.86,
    },
    {
        "pattern": re.compile(r"(?:distress|struggling|suffering|pain|hurting)", re.IGNORECASE),
        "domain": "distress",
        "value": "moderate",
        "confidence": 0.83,
    },
    {
        "pattern": re.compile(r"(?:family\s+(?:helps?|support|there\s+for\s+me))", re.IGNORECASE),
        "domain": "family_support",
        "value": "adequate",
        "confidence": 0.80,
    },
    {
        "pattern": re.compile(r"(?:hearing|court|trial|legal)", re.IGNORECASE),
        "domain": "hearing",
        "value": "mentioned",
        "confidence": 0.78,
    },
]


class MockLLMProvider:
    """
    Deterministic mock LLM provider for testing.

    Generates predictable empathetic responses and extracts candidate
    observations using simple keyword-matching rules. No API calls needed.

    Conforms to LLMProviderProtocol.
    """

    def __init__(
        self,
        default_reply: Optional[str] = None,
        enable_extraction: bool = True,
    ):
        """
        Parameters
        ----------
        default_reply : Optional[str]
            Custom default response text. If None, uses a natural default.
        enable_extraction : bool
            If True, applies keyword rules to extract candidate observations.
        """
        self.default_reply = default_reply or (
            "I hear you, and I appreciate you sharing that with me. "
            "It sounds like things have been really tough. "
            "What has been weighing on you the most?"
        )
        self.enable_extraction = enable_extraction
        self.call_count = 0
        self.last_message: Optional[str] = None

    def generate_response(
        self,
        message: str,
        state: MedhaState,
        next_question: Optional[QuestionRecord] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates a deterministic response with optional keyword-based observation extraction.

        Parameters
        ----------
        message : str
            Current user message.
        state : MedhaState
            Current session state.
        next_question : Optional[QuestionRecord]
            Optional question from the Question Engine.

        Returns
        -------
        LLMResponse
            Structured response with text and candidate observations.
        """
        self.call_count += 1
        self.last_message = message

        # Generate response text
        if next_question and next_question.question_text:
            response_text = (
                f"Thank you for sharing that. "
                f"If you feel comfortable, could you tell me: "
                f"{next_question.question_text}"
            )
        else:
            response_text = self.default_reply

        # Extract candidate observations using keyword rules
        observations: List[Dict[str, Any]] = []
        if self.enable_extraction and message and message.strip():
            for rule in _KEYWORD_RULES:
                match = rule["pattern"].search(message)
                if match:
                    observations.append({
                        "domain": rule["domain"],
                        "value": rule["value"],
                        "evidence": match.group(0),
                        "confidence": rule["confidence"],
                        "source": "llm_mock",
                    })

        return LLMResponse(
            text=response_text,
            candidate_observations=observations,
            metadata={
                "provider": "mock",
                "model": "mock_deterministic",
            },
        )
