"""
MEDHA Chatbot Safety Trigger & Alert Engine Integration
=========================================================

An additive safety layer that detects explicit immediate safety concerns and 
emits structured events to a backend Alert Engine, without interrupting the 
normal conversational or longitudinal MEDHA V2 predictive pipeline.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from chatbot.state.medha_state import MedhaState
from chatbot.interfaces import LLMProviderProtocol

logger = logging.getLogger(__name__)


def _current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


# ===========================================================================
# 1. SAFETY EVENT SCHEMA
# ===========================================================================

@dataclass
class SafetyEvent:
    """Structured payload for an immediate safety concern."""
    case_id: str
    source: str = "chatbot"
    safety_trigger: bool = True
    trigger_type: str = "immediate_danger"
    confidence: Optional[float] = None
    timestamp: str = field(default_factory=_current_iso_timestamp)
    session_id: Optional[str] = None
    evidence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "source": self.source,
            "safety_trigger": self.safety_trigger,
            "trigger_type": self.trigger_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "evidence": self.evidence,
        }


# ===========================================================================
# 2. ALERT ENGINE PROTOCOL
# ===========================================================================

@runtime_checkable
class AlertEngineProtocol(Protocol):
    """Protocol for delivering safety events to the backend."""
    def emit_safety_event(self, event: SafetyEvent) -> bool:
        """Returns True if successfully delivered/queued."""
        ...


class MockAlertEngine(AlertEngineProtocol):
    """
    Mock implementation of the Alert Engine for local deployment and testing.
    Records events in memory.
    """
    def __init__(self):
        self.emitted_events: list[SafetyEvent] = []

    def emit_safety_event(self, event: SafetyEvent) -> bool:
        logger.warning(f"URGENT ALERT DELIVERED: {event.trigger_type} for case {event.case_id}")
        self.emitted_events.append(copy.deepcopy(event))
        return True


# ===========================================================================
# 3. SAFETY TRIGGER
# ===========================================================================

class SafetyTrigger:
    """
    Evaluates every user message for explicit immediate safety concerns using
    the provided LLM provider. Emits events to the Alert Engine if detected.
    """

    # Allowed trigger types (Strict Schema)
    ALLOWED_TRIGGERS = {
        "immediate_danger",
        "self_harm_intent",
        "suicidal_intent",
        "threat_to_other",
        "immediate_protection_concern"
    }

    def __init__(self, alert_engine: Optional[AlertEngineProtocol] = None):
        """
        Parameters
        ----------
        alert_engine : Optional[AlertEngineProtocol]
            The engine to receive the safety events. Defaults to MockAlertEngine.
        """
        self.alert_engine = alert_engine or MockAlertEngine()

    def evaluate(
        self, 
        message: str, 
        state: MedhaState, 
        llm_provider: Optional[LLMProviderProtocol] = None
    ) -> Optional[SafetyEvent]:
        """
        Evaluates the message. If an explicit immediate concern is detected,
        creates a SafetyEvent, emits it to the Alert Engine, and logs it in MedhaState.
        
        Returns the event if triggered, else None.
        """
        # If no message or no LLM provider, we cannot perform classification
        if not message.strip() or not llm_provider:
            return None

        # Perform classification using LLM provider
        classification = self._classify_with_llm(message, llm_provider)

        if not classification or not classification.get("safety_trigger", False):
            return None

        trigger_type = classification.get("trigger_type")
        if trigger_type not in self.ALLOWED_TRIGGERS:
            # Enforce strict schema; do not invent types
            return None

        # Build SafetyEvent
        event = SafetyEvent(
            case_id=state.victim_id,
            session_id=state.session_id,
            trigger_type=trigger_type,
            evidence=classification.get("evidence", message),
            confidence=classification.get("confidence")
        )

        # Idempotency check: Don't emit if an identical trigger happened very recently
        if self._is_duplicate(event, state):
            return None

        # Emit to Alert Engine
        try:
            success = self.alert_engine.emit_safety_event(event)
            if not success:
                logger.error("AlertEngine refused or failed to process safety event.")
        except Exception as e:
            logger.error(f"AlertEngine integration failed: {e}")
            # Do not crash the chatbot pipeline

        # Log to MedhaState
        state.add_safety_event(event.to_dict())

        return event

    def _classify_with_llm(self, message: str, llm_provider: LLMProviderProtocol) -> Optional[Dict[str, Any]]:
        """Uses the LLM to classify explicit safety intents deterministically."""
        
        prompt = (
            "Analyze the following user message for EXPLICIT IMMEDIATE safety concerns.\n"
            "Do NOT trigger for normal sadness, general stress, or past events.\n"
            "Check for clear context and negations (e.g. 'I am not suicidal' is NOT a trigger).\n\n"
            "Allowed trigger_type values ONLY: [immediate_danger, self_harm_intent, suicidal_intent, threat_to_other, immediate_protection_concern]\n\n"
            "Return a strictly formatted JSON object with the following schema:\n"
            "{\n"
            '  "safety_trigger": bool, // true ONLY if there is an explicit immediate emergency\n'
            '  "trigger_type": str,    // must be one of the allowed values, or null if false\n'
            '  "evidence": str,        // quote from message justifying the trigger\n'
            '  "confidence": float     // between 0.0 and 1.0 representing confidence in classification\n'
            "}\n\n"
            f"User message: \"{message}\"\n\nJSON:"
        )

        try:
            # Some LLM providers might support generic prompt injection, if not, we fallback
            if hasattr(llm_provider, "extract_structured_fields"):
                schema = {
                    "type": "object",
                    "properties": {
                        "safety_trigger": {"type": "boolean"},
                        "trigger_type": {"type": "string"},
                        "evidence": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
                result = llm_provider.extract_structured_fields(prompt, target_schema=schema)
                return result
            
            # Since GeminiProvider in this project might not expose extract_structured_fields explicitly,
            # we can use generate_response as a fallback to get raw text and parse JSON if needed,
            # but ideally the provider has a JSON extraction method.
            if hasattr(llm_provider, "_extract_json_from_text") and hasattr(llm_provider, "client"):
                # Use Gemini client directly for this specialized classification
                response = llm_provider.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                return llm_provider._extract_json_from_text(response.text)
                
            return None
            
        except Exception as e:
            logger.error(f"Safety classification failed: {e}")
            return None

    def _is_duplicate(self, event: SafetyEvent, state: MedhaState) -> bool:
        """Lightweight idempotency: prevent identical triggers in the same session."""
        for past_event in state.safety_events[-5:]:
            if past_event.get("trigger_type") == event.trigger_type:
                # Same trigger type within recent history
                return True
        return False
