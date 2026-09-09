"""
MEDHA Explainability Engine
===========================
Converts multi-modal risk and context signals into deterministic,
support-oriented, non-diagnostic explanations for victims, counsellors, and administrators.
"""

from .schemas import (
    RiskLevel,
    Trend,
    FactorType,
    SignalsInput,
    ContextInput,
    RecentActivityInput,
    ExplainabilityInput,
    Factor,
    ExplainabilityOutput,
)
from .explainability_engine import (
    ExplainabilityEngine,
    get_explanation,
    validate_safety_phrasing,
    FORBIDDEN_DIAGNOSTIC_TERMS,
)

__all__ = [
    "RiskLevel",
    "Trend",
    "FactorType",
    "SignalsInput",
    "ContextInput",
    "RecentActivityInput",
    "ExplainabilityInput",
    "Factor",
    "ExplainabilityOutput",
    "ExplainabilityEngine",
    "get_explanation",
    "validate_safety_phrasing",
    "FORBIDDEN_DIAGNOSTIC_TERMS",
]
