"""
Gemini LLM Provider
====================

Production provider using the Google Gemini API via the `google-genai` SDK.

ARCHITECTURAL INVARIANTS:
- Gemini-specific code is FULLY ISOLATED inside this file.
- ConversationManager and all other chatbot components depend only on
  LLMProviderProtocol / LLMResponse from chatbot.interfaces.
- No API keys are hardcoded. Keys are loaded from environment variables.
- The model name is configurable via MEDHA_LLM_MODEL.
- This provider MUST NOT generate V2 numeric features, DDS, risk scores,
  or clinical diagnoses.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from chatbot.interfaces import LLMResponse
from chatbot.state.medha_state import MedhaState, QuestionRecord
from chatbot.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from chatbot.llm.observation_schema import (
    CANDIDATE_OBSERVATION_DOMAINS,
    validate_observation_domain,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Default model — configurable via environment variable
DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _extract_json_from_text(text: str) -> Optional[dict]:
    """
    Robustly extract a JSON object from LLM output text.
    Handles cases where the model wraps JSON in markdown fences.
    """
    # Try direct parse first
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", stripped, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # Try finding first { ... } block
    brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _parse_observations(raw_observations: list) -> List[Dict[str, Any]]:
    """
    Validates and filters extracted observations against the controlled schema.

    Observations with invalid domains or missing evidence are dropped.
    Confidence values are clamped to [0.0, 1.0].
    """
    validated: List[Dict[str, Any]] = []

    for obs in raw_observations:
        if not isinstance(obs, dict):
            continue

        domain = str(obs.get("domain", "")).lower().strip()
        value = obs.get("value")
        evidence = obs.get("evidence")
        confidence = obs.get("confidence")

        # Domain must be in the controlled vocabulary
        if not validate_observation_domain(domain):
            logger.debug(
                f"Dropping observation with unknown domain '{domain}'"
            )
            continue

        # Evidence is mandatory
        if not evidence or not str(evidence).strip():
            logger.debug(
                f"Dropping observation for domain '{domain}': missing evidence"
            )
            continue

        # Value is mandatory
        if value is None or (isinstance(value, str) and not value.strip()):
            logger.debug(
                f"Dropping observation for domain '{domain}': missing value"
            )
            continue

        # Clamp confidence to [0.0, 1.0]
        if confidence is not None:
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = None

        validated.append({
            "domain": domain,
            "value": str(value).strip() if isinstance(value, str) else value,
            "evidence": str(evidence).strip(),
            "confidence": confidence,
            "source": "llm",
        })

    return validated


class GeminiProvider:
    """
    LLM provider using Google Gemini API.

    Configuration via environment variables:
    - GEMINI_API_KEY or GOOGLE_API_KEY: API key for authentication.
    - MEDHA_LLM_MODEL: Model name (default: gemini-2.5-flash).

    This class conforms to LLMProviderProtocol.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_history_turns: int = 6,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ):
        """
        Parameters
        ----------
        api_key : Optional[str]
            Gemini API key. Falls back to GEMINI_API_KEY or GOOGLE_API_KEY env vars.
        model_name : Optional[str]
            Gemini model identifier. Falls back to MEDHA_LLM_MODEL env var.
        max_history_turns : int
            Maximum recent history turns to include in context.
        temperature : float
            LLM temperature for response generation.
        max_output_tokens : int
            Maximum output tokens for the response.
        """
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model_name = model_name or os.getenv("MEDHA_LLM_MODEL", DEFAULT_MODEL)
        self._max_history_turns = max_history_turns
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = None

    @property
    def client(self):
        """Lazily initializes the Gemini client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    "Gemini API key not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY "
                    "environment variable, or pass api_key directly."
                )
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "google-genai package is required for GeminiProvider. "
                    "Install with: pip install google-genai"
                )
        return self._client

    def generate_response(
        self,
        message: str,
        state: MedhaState,
        next_question: Optional[QuestionRecord] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates a natural empathetic response and extracts candidate observations.

        Parameters
        ----------
        message : str
            Current user message.
        state : MedhaState
            Current session state (used for conversation history context only).
        next_question : Optional[QuestionRecord]
            Optional question from the Question Engine to weave into the response.

        Returns
        -------
        LLMResponse
            Structured response with text and candidate observations.
        """
        from google.genai import types

        # Check if caller passed a raw prompt or summarization request
        is_raw_prompt = kwargs.get("raw_mode", False) or message.startswith("You are a summarization engine") or "Return ONLY a JSON object" in message

        if is_raw_prompt:
            try:
                response = self.client.models.generate_content(
                    model=self._model_name,
                    contents=message,
                    config=types.GenerateContentConfig(
                        temperature=self._temperature,
                        max_output_tokens=self._max_output_tokens,
                        response_mime_type="application/json",
                    ),
                )
                raw_text = response.text if response.text else "{}"
                return LLMResponse(
                    text=raw_text,
                    candidate_observations=[],
                    metadata={
                        "provider": "gemini",
                        "model": self._model_name,
                        "raw_mode": True,
                    },
                )
            except Exception as e:
                logger.error(f"Gemini raw generation failed: {e}")
                return LLMResponse(
                    text="{}",
                    candidate_observations=[],
                    metadata={
                        "provider": "gemini",
                        "model": self._model_name,
                        "error": str(e),
                    },
                )

        # Build conversation context from state history
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in state.conversation_history
        ]

        user_prompt = build_user_prompt(
            message=message,
            conversation_history=history_dicts,
            max_history_turns=self._max_history_turns,
        )

        # Append question engine hint if present
        if next_question and next_question.question_text:
            user_prompt += (
                f"\n\n## Question to naturally incorporate:\n"
                f"If appropriate, you may naturally work this into your response: "
                f'"{next_question.question_text}"'
            )

        try:
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                    response_mime_type="application/json",
                ),
            )

            raw_text = response.text if response.text else ""

            # Parse structured JSON output
            parsed = _extract_json_from_text(raw_text)

            if parsed and isinstance(parsed, dict):
                response_text = parsed.get("response_text", "").strip()
                raw_observations = parsed.get("observations", [])
            else:
                # Fallback: treat the entire output as response text
                response_text = raw_text.strip()
                raw_observations = []

            # Validate observations against controlled schema
            validated_observations = _parse_observations(
                raw_observations if isinstance(raw_observations, list) else []
            )

            if not response_text:
                response_text = (
                    "I hear you, and I appreciate you sharing that with me. "
                    "How are things feeling for you right now?"
                )

            return LLMResponse(
                text=response_text,
                candidate_observations=validated_observations,
                metadata={
                    "provider": "gemini",
                    "model": self._model_name,
                },
            )

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return LLMResponse(
                text=(
                    "I'm here for you. Could you tell me a bit more about "
                    "how you're feeling right now?"
                ),
                candidate_observations=[],
                metadata={
                    "provider": "gemini",
                    "model": self._model_name,
                    "error": str(e),
                },
            )
