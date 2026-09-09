"""
MEDHA Deterministic Feature Mapper
==================================

Converts approved semantic candidate observations into valid MEDHA V2
structured feature updates ONLY when an authoritative mapping exists.

ARCHITECTURAL RULES:
1. DO NOT invent numeric scores for missing schemas.
   (e.g. `sleep = "poor"` must NOT be mapped to `Sleep = 3.0`).
2. Missing information remains missing (zero is NOT a valid substitute).
3. If an authoritative V2 mapping does not exist, the observation remains
   in `MedhaState.candidate_observations` but is NOT mapped to a V2 feature.
4. Existing authoritative structured responses (e.g. from actual check-ins)
   are never overwritten by conversational extraction.
"""

from typing import Any, Dict, List, Optional
import logging

from chatbot.state.medha_state import MedhaState
from chatbot.interfaces import FeatureMapperProtocol
from chatbot.llm.observation_schema import validate_observation_domain

logger = logging.getLogger(__name__)


class DeterministicFeatureMapper:
    """
    Deterministic rule-based mapping layer from semantic candidate observations
    to actual MEDHA V2 numeric/categorical features.
    
    Implements FeatureMapperProtocol.
    """

    def process_observations(
        self,
        state: MedhaState,
        candidate_observations: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Maps conversational candidate observations to V2 features if an
        authoritative mapping exists.

        If a domain lacks an authoritative mapping, it is deliberately rejected
        for mapping and remains as a candidate observation in the state.

        Returns:
            Dict[str, Any]: A report of mapped and rejected observations.
        """
        mapped_features: Dict[str, Any] = {}
        rejected_observations: List[Dict[str, Any]] = []

        for obs in candidate_observations:
            if not isinstance(obs, dict):
                continue
            
            domain = obs.get("domain", "").lower().strip()
            value = obs.get("value")
            
            # Must be a valid domain
            if not validate_observation_domain(domain):
                obs["mapping_status"] = "rejected_invalid_domain"
                rejected_observations.append(obs)
                continue

            # -------------------------------------------------------------
            # AUTHORITATIVE MAPPINGS
            # -------------------------------------------------------------
            
            # 1. Threat_Event (Categorical Indicator)
            # V2 Schema: 1 = Yes, 0 = No
            if domain == "threat_event":
                mapped_val = self._map_indicator(value)
                if mapped_val is not None:
                    # Check for authoritative structured conflict
                    # Assume checkins might set Threat_Event. If it is already set
                    # (not None or NaN), we do not overwrite conversational inference
                    # unless our policy allows it. Policy: Conversational doesn't override
                    # existing structured data if it already exists from a check-in.
                    # Since we don't know origin here perfectly, we check if it is populated.
                    if self._can_overwrite_feature(state, "structured", "Threat_Event"):
                        state.update_feature("structured", "Threat_Event", mapped_val)
                        mapped_features["Threat_Event"] = mapped_val
                        obs["status"] = "mapped"
                    else:
                        obs["mapping_status"] = "rejected_structured_conflict"
                        rejected_observations.append(obs)
                else:
                    obs["mapping_status"] = "rejected_invalid_value"
                    rejected_observations.append(obs)

            # 2. Recent_Episode (Categorical Indicator)
            # V2 Schema: 1 = Yes, 0 = No
            elif domain == "recent_episode":
                mapped_val = self._map_indicator(value)
                if mapped_val is not None:
                    if self._can_overwrite_feature(state, "structured", "Recent_Episode"):
                        state.update_feature("structured", "Recent_Episode", mapped_val)
                        mapped_features["Recent_Episode"] = mapped_val
                        obs["status"] = "mapped"
                    else:
                        obs["mapping_status"] = "rejected_structured_conflict"
                        rejected_observations.append(obs)
                else:
                    obs["mapping_status"] = "rejected_invalid_value"
                    rejected_observations.append(obs)

            # -------------------------------------------------------------
            # REJECTED MAPPINGS (No authoritative string->numeric schema)
            # -------------------------------------------------------------
            # Domains like mood, sleep, stress, fear, safety, etc.
            # V2 requires strict 1-5 ints/floats, but LLM provides qualitative strings.
            else:
                obs["mapping_status"] = "rejected_no_authoritative_mapping"
                rejected_observations.append(obs)

        return {
            "mapped_features": mapped_features,
            "rejected_observations": rejected_observations,
            "validation_errors": []
        }

    def _map_indicator(self, semantic_value: Any) -> Optional[float]:
        """Maps presence/absence semantic strings to V2 indicator float (1.0 or 0.0)."""
        if not isinstance(semantic_value, str):
            return None
            
        val = semantic_value.lower().strip()
        if val in ("present", "recent", "yes"):
            return 1.0
        elif val in ("absent", "none", "no"):
            return 0.0
        return None

    def _can_overwrite_feature(self, state: MedhaState, modality: str, feature_name: str) -> bool:
        """
        Determines if a conversational feature can overwrite an existing feature.
        Policy: Do not overwrite an existing, non-null value because it likely
        came from an authoritative source (like an active structured checkin).
        """
        if modality == "structured":
            import math
            val = state.structured_features.get(feature_name)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return True
            return False
        return False
