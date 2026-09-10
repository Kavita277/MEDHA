"""
MEDHA Chatbot Interfaces & Protocols
====================================

Defines abstract protocols and lightweight default/placeholder implementations
for pluggable chatbot components:
1. LLM Provider (generates natural responses without clinical scoring)
2. Safety Gateway (deterministic crisis/safety routing)
3. Question Engine (controlled question policy)
4. Feature Mapper (authoritative V2 observation mapping)
5. Text Adapter (existing frozen Text Engine interface)

ABSOLUTE ARCHITECTURAL RULE:
No component in this module or the conversation manager may:
- Calculate DDS
- Calculate future risk
- Generate clinical diagnoses
- Select or fabricate numerical risk scores
- Implement fusion models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from chatbot.state.medha_state import MedhaState, QuestionRecord
from chatbot.engines.text_adapter import TextEngineResult


# ===========================================================================
# 1. LLM PROVIDER PROTOCOL & PLACEHOLDER
# ===========================================================================

@dataclass
class LLMResponse:
    """Standardized response from the LLM layer."""
    text: str
    candidate_observations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Protocol for pluggable conversational LLM providers."""

    def generate_response(
        self,
        message: str,
        state: MedhaState,
        next_question: Optional[QuestionRecord] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generates an empathetic response without fabricating scores or diagnoses."""
        ...


class PlaceholderLLMProvider:
    """
    Default placeholder LLM provider for early integration steps.
    Returns supportive acknowledgments without clinical claims or scoring.
    """

    def __init__(self, default_reply: Optional[str] = None):
        self.default_reply = default_reply or (
            "I hear you, and I am here with you. Thank you for sharing that with me. "
            "How are things feeling for you right now?"
        )

    def generate_response(
        self,
        message: str,
        state: MedhaState,
        next_question: Optional[QuestionRecord] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if next_question and hasattr(next_question, "question_text") and next_question.question_text:
            text = f"I understand. If you feel comfortable answering: {next_question.question_text}"
        else:
            text = self.default_reply

        return LLMResponse(
            text=text,
            candidate_observations=[],
            metadata={"provider": "placeholder"},
        )


# ===========================================================================
# 2. SAFETY GATEWAY PROTOCOL & PLACEHOLDER
# ===========================================================================

@dataclass
class SafetyResult:
    """Standardized evaluation result from the Safety Gateway."""
    is_triggered: bool = False
    category: Optional[str] = None
    crisis_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SafetyGatewayProtocol(Protocol):
    """Protocol for deterministic safety and crisis routing."""

    def evaluate(
        self,
        message: str,
        state: MedhaState,
        **kwargs: Any,
    ) -> SafetyResult:
        """Evaluates whether message indicates immediate danger or severe crisis."""
        ...


class PassThroughSafetyGateway(SafetyGatewayProtocol):
    """
    Default pass-through safety gateway.
    Returns non-triggered result until Step 8 implements full deterministic rules.
    """

    def evaluate(
        self,
        message: str,
        state: MedhaState,
        **kwargs: Any,
    ) -> SafetyResult:
        return SafetyResult(is_triggered=False)


# ===========================================================================
# SUMMARY ENGINE PROTOCOL (Step 9)
# ===========================================================================

class SummaryEngineProtocol(Protocol):
    """
    Updates the conversation summary state deterministically.
    """
    def update_summary(self, state: MedhaState, llm_provider: LLMProviderProtocol, **kwargs: Any) -> None:
        """Updates state.conversation_summary based on recent conversation."""
        ...


class PassThroughSummaryEngine(SummaryEngineProtocol):
    def update_summary(self, state: MedhaState, llm_provider: LLMProviderProtocol, **kwargs: Any) -> None:
        pass


# ===========================================================================
# 3. QUESTION ENGINE PROTOCOL & PLACEHOLDER
# ===========================================================================

@runtime_checkable
class QuestionEngineProtocol(Protocol):
    """Protocol for controlled question bank selection with cooldowns."""

    def select_next_question(
        self,
        state: MedhaState,
        **kwargs: Any,
    ) -> Optional[QuestionRecord]:
        """Selects the next question from approved bank, or None if flow complete."""
        ...


class PassThroughQuestionEngine:
    """
    Default pass-through question engine.
    Returns None until Step 7 implements the controlled question bank policy.
    """

    def select_next_question(
        self,
        state: MedhaState,
        **kwargs: Any,
    ) -> Optional[QuestionRecord]:
        return None


# ===========================================================================
# 4. FEATURE MAPPER PROTOCOL & PLACEHOLDER
# ===========================================================================

@runtime_checkable
class FeatureMapperProtocol(Protocol):
    """Protocol for authoritative V2 structured feature mapping."""

    def process_observations(
        self,
        state: MedhaState,
        candidate_observations: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Maps candidate observations into authoritative V2 features."""
        ...


class PassThroughFeatureMapper:
    """
    Default pass-through feature mapper.
    Does not invent numbers or mappings until Step 6.
    """

    def process_observations(
        self,
        state: MedhaState,
        candidate_observations: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return {}


# ===========================================================================
# 5. TEXT ADAPTER PROTOCOL
# ===========================================================================

@runtime_checkable
class TextAdapterProtocol(Protocol):
    """Protocol for the existing frozen Text Engine adapter."""

    def process_and_update_state(
        self,
        state: MedhaState,
        text: Optional[str],
        language: Optional[str] = None,
        source: str = "chatbot",
    ) -> TextEngineResult:
        """Processes conversational text and updates MedhaState atomically."""
        ...


# ===========================================================================
# 6. BEHAVIOUR ADAPTER PROTOCOL
# ===========================================================================

@runtime_checkable
class BehaviourAdapterProtocol(Protocol):
    """
    Protocol for processing authoritative behaviour data.
    Validates and populates MedhaState.behaviour_features.
    Does NOT invoke ML inference natively (V2 pipeline owns inference).
    """

    def process_and_update_state(
        self,
        state: MedhaState,
        behaviour_data: Dict[str, Any],
    ) -> None:
        """
        Validates behaviour input and updates canonical V2 behaviour features in state.
        """
        ...


class PassThroughBehaviourAdapter:
    """Default placeholder that treats behaviour data as unavailable."""
    def process_and_update_state(
        self,
        state: MedhaState,
        behaviour_data: Dict[str, Any],
    ) -> None:
        for feat in state.behaviour_features:
            state.behaviour_features[feat] = None
        state.set_modality_availability("behaviour", 0.0)


# ===========================================================================
# 7. VOICE ADAPTER PROTOCOL
# ===========================================================================

@runtime_checkable
class VoiceAdapterProtocol(Protocol):
    """
    Protocol for the existing frozen Voice Engine adapter.
    """

    def process_and_update_state(
        self,
        state: MedhaState,
        audio_path: Optional[str],
    ) -> None:
        """Processes conversational audio and updates MedhaState atomically."""
        ...


class PassThroughVoiceAdapter:
    """Default placeholder that treats voice data as unavailable."""
    def process_and_update_state(
        self,
        state: MedhaState,
        audio_path: Optional[str],
    ) -> None:
        if audio_path is None:
            return
        for feat in state.voice_features:
            state.voice_features[feat] = None
        state.set_modality_availability("voice", 0.0)
