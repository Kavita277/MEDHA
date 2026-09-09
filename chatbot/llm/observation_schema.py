"""
Candidate Observation Schema
=============================

Controlled vocabulary for semantic observation extraction by the LLM.

CRITICAL DISTINCTION:
- A **candidate observation** is a qualitative note about what the user appears
  to have said (e.g., sleep → poor). It carries semantic_value and evidence.
- A **V2 feature** is a validated numeric/category value accepted by
  MedhaV2Adapter (e.g., Sleep = 3.0).

These MUST remain separate until Step 6 (Feature Mapper + Validator) provides
authoritative mappings.

The LLM MUST NOT:
- Generate V2 numeric feature values
- Fabricate DDS, risk scores, or probabilities
- Assign arbitrary 0–1 floats for V2 columns
- Invent observations without user-message evidence
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Optional, Tuple

# ---------------------------------------------------------------------------
# Controlled candidate-observation domains
# ---------------------------------------------------------------------------
# Derived from the existing MEDHA V2 structured + specialist feature registries.
# Each domain name is a semantic concept the LLM may recognise in conversation.
# The LLM must NOT extend this list at runtime.

CANDIDATE_OBSERVATION_DOMAINS: FrozenSet[str] = frozenset({
    # Core self-report domains (V2 structured checkin features)
    "mood",
    "stress",
    "sleep",
    "functioning",
    "safety",
    "social_support",
    "wellbeing",

    # Protective / contextual factors
    "family_support",
    "therapist_engagement",
    "access_to_services",
    "stable_housing",

    # Event / situational context
    "threat_event",
    "hearing",
    "investigation_delay",
    "compensation_delay",
    "relocation_stress",
    "rehabilitation_issue",
    "protection_event",
    "recent_episode",

    # Text-engine–aligned emotional domains
    "fear",
    "distress",
    "urgency",
    "negative_affect",
    "threat_context",
})


# Allowed semantic values per domain.
# If a domain is NOT listed here, any free-text value is accepted
# (the LLM should still keep values descriptive and evidence-backed).
ALLOWED_SEMANTIC_VALUES: Dict[str, Tuple[str, ...]] = {
    "mood": ("very_low", "low", "neutral", "positive", "very_positive"),
    "stress": ("none", "mild", "moderate", "high", "severe"),
    "sleep": ("good", "fair", "poor", "very_poor", "absent"),
    "functioning": ("normal", "mildly_impaired", "moderately_impaired", "severely_impaired"),
    "safety": ("safe", "uncertain", "unsafe", "in_danger"),
    "social_support": ("strong", "adequate", "reduced", "isolated"),
    "wellbeing": ("good", "fair", "poor", "very_poor"),
    "family_support": ("strong", "adequate", "weak", "absent"),
    "fear": ("absent", "mild", "moderate", "severe", "present"),
    "distress": ("absent", "mild", "moderate", "severe"),
    "urgency": ("none", "low", "moderate", "high", "critical"),
    "negative_affect": ("absent", "mild", "moderate", "severe"),
    "threat_event": ("present", "absent", "recent"),
    "recent_episode": ("present", "absent"),
}


def validate_observation_domain(domain: str) -> bool:
    """Returns True if the domain is in the controlled vocabulary."""
    return domain.lower().strip() in CANDIDATE_OBSERVATION_DOMAINS


def validate_semantic_value(domain: str, value: str) -> bool:
    """
    Returns True if the semantic value is acceptable for the domain.
    If the domain has no restricted vocabulary, any non-empty string is accepted.
    """
    domain_clean = domain.lower().strip()
    if domain_clean not in ALLOWED_SEMANTIC_VALUES:
        return bool(value and str(value).strip())
    return str(value).lower().strip() in ALLOWED_SEMANTIC_VALUES[domain_clean]
