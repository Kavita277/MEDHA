"""
schemas.py
==========
Data schemas and type definitions for MEDHA's Recommendation + Intervention Engine.

Defines input and output data structures, enums (including the 5 QuestionEngine intents),
and serialization helpers.
Designed to be dependency-free (using Python standard library dataclasses),
deterministic, and easily convertible to/from plain dictionaries and JSON.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Sequence


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_str(cls, value: str) -> "RiskLevel":
        try:
            return cls[value.strip().upper()]
        except (KeyError, AttributeError):
            raise ValueError(f"Invalid RiskLevel: '{value}'. Must be one of {[e.value for e in cls]}")


class Trend(str, Enum):
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"

    @classmethod
    def from_str(cls, value: str) -> "Trend":
        try:
            return cls[value.strip().upper()]
        except (KeyError, AttributeError):
            raise ValueError(f"Invalid Trend: '{value}'. Must be one of {[e.value for e in cls]}")


class Priority(str, Enum):
    ROUTINE = "ROUTINE"
    INCREASED = "INCREASED"
    PRIORITY = "PRIORITY"
    URGENT = "URGENT"
    IMMEDIATE = "IMMEDIATE"


class Category(str, Enum):
    MONITORING = "monitoring"
    COUNSELLING = "counselling"
    INTERVENTION = "intervention"
    PROTECTION = "protection"
    LEGAL_SUPPORT = "legal_support"
    FINANCIAL_SUPPORT = "financial_support"
    REHABILITATION = "rehabilitation"
    ESCALATION = "escalation"


class Intent(str, Enum):
    """
    The five core Question Engine intents defined in MEDHA:
    1. safety_support
    2. event_related_stress
    3. sleep_functioning
    4. social_emotional_support
    5. general_wellbeing
    """
    SAFETY_SUPPORT = "safety_support"
    EVENT_RELATED_STRESS = "event_related_stress"
    SLEEP_FUNCTIONING = "sleep_functioning"
    SOCIAL_EMOTIONAL_SUPPORT = "social_emotional_support"
    GENERAL_WELLBEING = "general_wellbeing"

    @classmethod
    def from_str(cls, value: str) -> "Intent":
        val = str(value).strip().lower()
        for member in cls:
            if member.value == val or member.name.lower() == val:
                return member
        raise ValueError(
            f"Invalid Intent: '{value}'. Must be one of {[e.value for e in cls]}"
        )


@dataclass
class SignalsInput:
    text_distress: float = 0.0
    voice_distress: float = 0.0
    behavioural_risk: float = 0.0
    structured_risk: float = 0.0
    temporal_risk: float = 0.0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SignalsInput":
        if not data:
            return cls()
        return cls(
            text_distress=float(data.get("text_distress", 0.0)),
            voice_distress=float(data.get("voice_distress", 0.0)),
            behavioural_risk=float(data.get("behavioural_risk", 0.0)),
            structured_risk=float(data.get("structured_risk", 0.0)),
            temporal_risk=float(data.get("temporal_risk", 0.0)),
        )

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class ContextInput:
    threat_event: bool = False
    investigation_delay: bool = False
    compensation_delay: bool = False
    financial_hardship: bool = False
    rehabilitation_issue: bool = False
    protection_issue: bool = False

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ContextInput":
        if not data:
            return cls()
        return cls(
            threat_event=bool(data.get("threat_event", False)),
            investigation_delay=bool(data.get("investigation_delay", False)),
            compensation_delay=bool(data.get("compensation_delay", False)),
            financial_hardship=bool(data.get("financial_hardship", False)),
            rehabilitation_issue=bool(data.get("rehabilitation_issue", False)),
            protection_issue=bool(data.get("protection_issue", False)),
        )

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)


@dataclass
class RecommendationEngineInput:
    case_id: str
    fused_risk_score: float
    risk_level: RiskLevel
    trend: Trend
    signals: SignalsInput = field(default_factory=SignalsInput)
    context: ContextInput = field(default_factory=ContextInput)
    intent: Optional[Union[Intent, List[Intent]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationEngineInput":
        if not isinstance(data, dict):
            raise TypeError(f"Input must be a dict, got {type(data).__name__}")

        case_id = str(data.get("case_id", "UNKNOWN"))
        fused_risk_score = float(data.get("fused_risk_score", 0.0))
        
        raw_risk_level = data.get("risk_level", "LOW")
        risk_level = (
            raw_risk_level if isinstance(raw_risk_level, RiskLevel) 
            else RiskLevel.from_str(str(raw_risk_level))
        )

        raw_trend = data.get("trend", "STABLE")
        trend = (
            raw_trend if isinstance(raw_trend, Trend)
            else Trend.from_str(str(raw_trend))
        )

        raw_signals = data.get("signals", {})
        signals = (
            raw_signals if isinstance(raw_signals, SignalsInput)
            else SignalsInput.from_dict(raw_signals)
        )

        raw_context = data.get("context", {})
        context = (
            raw_context if isinstance(raw_context, ContextInput)
            else ContextInput.from_dict(raw_context)
        )

        # Parse intent if present (supports single intent or list of intents)
        raw_intent = data.get("intent") or data.get("intents") or data.get("active_intent")
        parsed_intent: Optional[Union[Intent, List[Intent]]] = None
        if raw_intent is not None:
            if isinstance(raw_intent, (list, tuple, set)):
                parsed_intent = [
                    i if isinstance(i, Intent) else Intent.from_str(str(i))
                    for i in raw_intent
                ]
            else:
                parsed_intent = (
                    raw_intent if isinstance(raw_intent, Intent)
                    else Intent.from_str(str(raw_intent))
                )

        return cls(
            case_id=case_id,
            fused_risk_score=fused_risk_score,
            risk_level=risk_level,
            trend=trend,
            signals=signals,
            context=context,
            intent=parsed_intent,
        )

    def to_dict(self) -> Dict[str, Any]:
        intent_val = None
        if self.intent is not None:
            if isinstance(self.intent, list):
                intent_val = [i.value for i in self.intent]
            elif isinstance(self.intent, Intent):
                intent_val = self.intent.value
            else:
                intent_val = str(self.intent)

        res = {
            "case_id": self.case_id,
            "fused_risk_score": self.fused_risk_score,
            "risk_level": self.risk_level.value,
            "trend": self.trend.value,
            "signals": self.signals.to_dict(),
            "context": self.context.to_dict(),
        }
        if intent_val is not None:
            res["intent"] = intent_val
        return res


@dataclass
class Recommendation:
    id: str
    category: str
    priority: str
    reason: str
    action: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "category": self.category,
            "priority": self.priority,
            "reason": self.reason,
            "action": self.action,
        }


@dataclass
class SelfHelpResource:
    id: str
    type: str
    title: str
    category: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "category": self.category,
            "description": self.description,
        }


@dataclass
class RecommendationEngineOutput:
    case_id: str
    risk_level: str
    recommendations: List[Recommendation] = field(default_factory=list)
    self_help: List[SelfHelpResource] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "risk_level": self.risk_level,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "self_help": [s.to_dict() for s in self.self_help],
        }
