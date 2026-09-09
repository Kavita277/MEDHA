"""
Deterministic Safety Gateway
============================

Evaluates whether a conversation contains a safety-critical signal based purely on 
explicit, deterministic rules. Separates conversational safety from predictive ML risk.
"""

import logging
from typing import Any

from chatbot.interfaces import SafetyGatewayProtocol, SafetyResult
from chatbot.state.medha_state import MedhaState

logger = logging.getLogger(__name__)


class DeterministicSafetyGateway(SafetyGatewayProtocol):
    """
    Deterministic rule-based policy for safety escalation.
    
    Rules:
    1. Check candidate_observations for explicit safety/threat/urgency flags.
    2. Check structured_features for authoritative Threat_Event or Recent_Episode.
    3. Missing data means no trigger.
    4. High V2 ML risk scores DO NOT trigger this gateway.
    """

    def evaluate(
        self,
        message: str,
        state: MedhaState,
        **kwargs: Any,
    ) -> SafetyResult:
        """
        Evaluates the current state and message for safety triggers.
        """
        
        # 1. Check candidate observations
        for obs in state.candidate_observations:
            domain = obs.domain
            val = obs.semantic_value
            
            # Semantic values mapping to emergency
            if domain == "safety" and val in ["unsafe", "in_danger"]:
                return self._create_trigger_result(
                    category="conversational_safety",
                    source="candidate_observation",
                    evidence=f"domain: safety, value: {val}, evidence: {obs.evidence}"
                )
                
            if domain == "threat_event" and val == "present":
                return self._create_trigger_result(
                    category="conversational_threat",
                    source="candidate_observation",
                    evidence=f"domain: threat_event, value: {val}, evidence: {obs.evidence}"
                )
                
            if domain == "urgency" and val == "critical":
                return self._create_trigger_result(
                    category="conversational_urgency",
                    source="candidate_observation",
                    evidence=f"domain: urgency, value: {val}, evidence: {obs.evidence}"
                )

        # 2. Check authoritative structured features
        # Note: 'Safety' structured feature's numeric threshold is undocumented, 
        # so we do not infer emergency from it.
        
        threat_event = state.structured_features.get("Threat_Event")
        if threat_event == 1.0:
            return self._create_trigger_result(
                category="structured_threat",
                source="structured",
                evidence="Threat_Event == 1.0"
            )
            
        recent_episode = state.structured_features.get("Recent_Episode")
        if recent_episode == 1.0:
            return self._create_trigger_result(
                category="structured_episode",
                source="structured",
                evidence="Recent_Episode == 1.0"
            )

        # No triggers found
        return SafetyResult(is_triggered=False)

    def _create_trigger_result(self, category: str, source: str, evidence: str) -> SafetyResult:
        crisis_text = (
            "I hear you, and your safety is the highest priority. "
            "Please connect immediately with a crisis helpline or a trusted professional."
        )
        return SafetyResult(
            is_triggered=True,
            category=category,
            crisis_response=crisis_text,
            metadata={
                "source": source,
                "evidence": evidence
            }
        )
