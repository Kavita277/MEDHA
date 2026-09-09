"""
MEDHA Alert Engine
==================
Evaluates risk assessments and contextual signals downstream to determine
alert triggers, priorities, safe support notifications, and CTAs.
"""

from .schemas import (
    RiskLevel,
    Trend,
    AlertPriority,
    AlertType,
    AlertStatus,
    ReasonCode,
    SignalsInput,
    ContextInput,
    AlertInput,
    AlertOutput,
)
from .alert_engine import (
    AlertEngine,
    get_alert,
    is_duplicate_alert,
    evaluate_conversational_safety,
    EXPLICIT_SAFETY_KEYWORDS,
    MODALITY_DISTRESS_THRESHOLD,
)

__all__ = [
    "RiskLevel",
    "Trend",
    "AlertPriority",
    "AlertType",
    "AlertStatus",
    "ReasonCode",
    "SignalsInput",
    "ContextInput",
    "AlertInput",
    "AlertOutput",
    "AlertEngine",
    "get_alert",
    "is_duplicate_alert",
    "evaluate_conversational_safety",
    "EXPLICIT_SAFETY_KEYWORDS",
    "MODALITY_DISTRESS_THRESHOLD",
]
