"""
schemas.py
==========
Data schemas and type definitions for MEDHA's Explainability Engine.

Defines input and output data structures, enums, factor representations,
and serialization helpers.
Designed to be dependency-free (using Python standard library dataclasses),
deterministic, and easily convertible to/from plain dictionaries and JSON.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional, Union


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


class FactorType(str, Enum):
    TREND = "trend"
    TEXT = "text"
    VOICE = "voice"
    BEHAVIOUR = "behaviour"
    STRUCTURED = "structured"
    TEMPORAL = "temporal"
    CONTEXT = "context"
    ACTIVITY = "activity"


@dataclass
class SignalsInput:
    text_distress: Optional[float] = None
    voice_distress: Optional[float] = None
    behavioural_risk: Optional[float] = None
    structured_risk: Optional[float] = None
    temporal_risk: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SignalsInput":
        if not data:
            return cls()
        return cls(
            text_distress=float(data["text_distress"]) if "text_distress" in data and data["text_distress"] is not None else None,
            voice_distress=float(data["voice_distress"]) if "voice_distress" in data and data["voice_distress"] is not None else None,
            behavioural_risk=float(data["behavioural_risk"]) if "behavioural_risk" in data and data["behavioural_risk"] is not None else None,
            structured_risk=float(data["structured_risk"]) if "structured_risk" in data and data["structured_risk"] is not None else None,
            temporal_risk=float(data["temporal_risk"]) if "temporal_risk" in data and data["temporal_risk"] is not None else None,
        )

    def to_dict(self) -> Dict[str, Optional[float]]:
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
class RecentActivityInput:
    checkins: int = 0
    journal_entries: int = 0
    voice_interactions: int = 0
    text_interactions: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "RecentActivityInput":
        if not data:
            return cls()
        return cls(
            checkins=int(data.get("checkins", 0)),
            journal_entries=int(data.get("journal_entries", 0)),
            voice_interactions=int(data.get("voice_interactions", 0)),
            text_interactions=int(data.get("text_interactions", 0)),
        )

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class ExplainabilityInput:
    case_id: str
    fused_risk_score: float
    risk_level: RiskLevel
    trend: Trend = Trend.STABLE
    signals: SignalsInput = field(default_factory=SignalsInput)
    context: ContextInput = field(default_factory=ContextInput)
    recent_activity: Optional[RecentActivityInput] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExplainabilityInput":
        if not isinstance(data, dict):
            raise TypeError(f"Input must be a dict, got {type(data).__name__}")

        if "case_id" not in data:
            raise ValueError("Missing required field: 'case_id'")
        case_id = str(data["case_id"])

        if "fused_risk_score" not in data:
            raise ValueError("Missing required field: 'fused_risk_score'")
        fused_risk_score = float(data["fused_risk_score"])

        if "risk_level" not in data:
            raise ValueError("Missing required field: 'risk_level'")
        raw_risk_level = data["risk_level"]
        risk_level = (
            raw_risk_level if isinstance(raw_risk_level, RiskLevel)
            else RiskLevel.from_str(str(raw_risk_level))
        )

        raw_trend = data.get("trend", "STABLE")
        trend = (
            raw_trend if isinstance(raw_trend, Trend)
            else Trend.from_str(str(raw_trend))
        )

        raw_signals = data.get("signals")
        signals = (
            raw_signals if isinstance(raw_signals, SignalsInput)
            else SignalsInput.from_dict(raw_signals)
        )

        raw_context = data.get("context")
        context = (
            raw_context if isinstance(raw_context, ContextInput)
            else ContextInput.from_dict(raw_context)
        )

        raw_activity = data.get("recent_activity")
        recent_activity = (
            raw_activity if isinstance(raw_activity, RecentActivityInput)
            else RecentActivityInput.from_dict(raw_activity) if raw_activity is not None else None
        )

        return cls(
            case_id=case_id,
            fused_risk_score=fused_risk_score,
            risk_level=risk_level,
            trend=trend,
            signals=signals,
            context=context,
            recent_activity=recent_activity,
        )

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "case_id": self.case_id,
            "fused_risk_score": self.fused_risk_score,
            "risk_level": self.risk_level.value,
            "trend": self.trend.value,
            "signals": self.signals.to_dict(),
            "context": self.context.to_dict(),
        }
        if self.recent_activity is not None:
            res["recent_activity"] = self.recent_activity.to_dict()
        return res


@dataclass
class Factor:
    factor: str
    description: str
    type: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "factor": self.factor,
            "description": self.description,
            "type": self.type,
        }


@dataclass
class ExplainabilityOutput:
    case_id: str
    summary: str
    factors: List[Factor] = field(default_factory=list)
    trend_explanation: str = ""
    disclaimer: str = "This is a support-oriented explanation and is not a medical diagnosis."
    risk_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "case_id": self.case_id,
            "summary": self.summary,
            "factors": [f.to_dict() for f in self.factors],
            "trend_explanation": self.trend_explanation,
            "disclaimer": self.disclaimer,
        }
        if self.risk_level is not None:
            res["risk_level"] = self.risk_level
        return res
