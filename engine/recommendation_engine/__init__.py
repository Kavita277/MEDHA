"""
MEDHA Recommendation + Intervention Engine
===========================================
Deterministic, rule-based recommendation engine for MEDHA victim support platform.
"""

from .schemas import (
    RiskLevel,
    Trend,
    Priority,
    Category,
    Intent,
    SignalsInput,
    ContextInput,
    RecommendationEngineInput,
    Recommendation,
    SelfHelpResource,
    RecommendationEngineOutput,
)
from .rules import (
    evaluate_base_risk_rules,
    evaluate_trend_rules,
    evaluate_context_rules,
    select_self_help_resources,
    validate_safety_phrasing,
)
from .recommendation_engine import (
    RecommendationEngine,
    get_recommendations,
)

__all__ = [
    "RiskLevel",
    "Trend",
    "Priority",
    "Category",
    "Intent",
    "SignalsInput",
    "ContextInput",
    "RecommendationEngineInput",
    "Recommendation",
    "SelfHelpResource",
    "RecommendationEngineOutput",
    "evaluate_base_risk_rules",
    "evaluate_trend_rules",
    "evaluate_context_rules",
    "select_self_help_resources",
    "validate_safety_phrasing",
    "RecommendationEngine",
    "get_recommendations",
]
