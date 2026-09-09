"""
schemas.py
==========
Data schemas and type definitions for MEDHA's Alert Engine.

Defines input and output data structures, enums (RiskLevel, Trend, AlertPriority,
AlertType, AlertStatus, ReasonCode), and serialization helpers.
Designed to be dependency-free (using Python standard library dataclasses),
deterministic, and easily convertible to/from plain dictionaries and JSON.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import hashlib


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


class AlertPriority(str, Enum):
    ROUTINE = "ROUTINE"
    ATTENTION = "ATTENTION"
    PRIORITY = "PRIORITY"
    URGENT = "URGENT"
    IMMEDIATE = "IMMEDIATE"


class AlertType(str, Enum):
    MONITORING = "MONITORING"
    SUPPORT_NOTIFICATION = "SUPPORT_NOTIFICATION"
    SUPPORT_RISK = "SUPPORT_RISK"
    SAFETY_ESCALATION = "SAFETY_ESCALATION"
    CRISIS_ESCALATION = "CRISIS_ESCALATION"


class AlertStatus(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class ReasonCode(str, Enum):
    # Risk Level Codes
    LOW_RISK = "LOW_RISK"
    MODERATE_RISK = "MODERATE_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL_RISK = "CRITICAL_RISK"

    # Trajectory Codes
    INCREASING_TREND = "INCREASING_TREND"
    STABLE_TREND = "STABLE_TREND"
    DECREASING_TREND = "DECREASING_TREND"

    # Contextual Codes
    THREAT_REPORTED = "THREAT_REPORTED"
    PROTECTION_CONCERN = "PROTECTION_CONCERN"
    FINANCIAL_HARDSHIP = "FINANCIAL_HARDSHIP"
    REHABILITATION_ISSUE = "REHABILITATION_ISSUE"
    INVESTIGATION_DELAY = "INVESTIGATION_DELAY"
    COMPENSATION_DELAY = "COMPENSATION_DELAY"

    # Modality Distress Codes
    HIGH_TEXT_DISTRESS = "HIGH_TEXT_DISTRESS"
    HIGH_VOICE_DISTRESS = "HIGH_VOICE_DISTRESS"
    ELEVATED_BEHAVIOURAL_RISK = "ELEVATED_BEHAVIOURAL_RISK"
    HIGH_STRUCTURED_RISK = "HIGH_STRUCTURED_RISK"
    HIGH_TEMPORAL_RISK = "HIGH_TEMPORAL_RISK"


    # Conversational Fast-Path Codes
    CONVERSATIONAL_SAFETY_CONCERN = "CONVERSATIONAL_SAFETY_CONCERN"


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
class AlertInput:
    case_id: str
    risk_level: RiskLevel
    fused_risk_score: float = 0.0
    trend: Trend = Trend.STABLE
    signals: SignalsInput = field(default_factory=SignalsInput)
    context: ContextInput = field(default_factory=ContextInput)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertInput":
        if not isinstance(data, dict):
            raise TypeError(f"Input must be a dict, got {type(data).__name__}")

        if "case_id" not in data:
            raise ValueError("Missing required field: 'case_id'")
        case_id = str(data["case_id"])

        if "risk_level" not in data:
            raise ValueError("Missing required field: 'risk_level'")
        raw_risk_level = data["risk_level"]
        risk_level = (
            raw_risk_level if isinstance(raw_risk_level, RiskLevel)
            else RiskLevel.from_str(str(raw_risk_level))
        )

        fused_risk_score = float(data.get("fused_risk_score", 0.0))

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

        return cls(
            case_id=case_id,
            risk_level=risk_level,
            fused_risk_score=fused_risk_score,
            trend=trend,
            signals=signals,
            context=context,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "risk_level": self.risk_level.value,
            "fused_risk_score": self.fused_risk_score,
            "trend": self.trend.value,
            "signals": self.signals.to_dict(),
            "context": self.context.to_dict(),
        }


@dataclass
class AlertOutput:
    alert_id: str
    case_id: str
    alert_triggered: bool
    priority: str
    alert_type: str
    title: str
    message: str
    recommended_action: str
    cta: str
    reason: str = ""
    source: str = "fusion_pipeline"
    reason_codes: List[str] = field(default_factory=list)
    status: str = AlertStatus.NEW.value
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "case_id": self.case_id,
            "alert_triggered": self.alert_triggered,
            "priority": self.priority,
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "reason": self.reason,
            "source": self.source,
            "recommended_action": self.recommended_action,
            "cta": self.cta,
            "reason_codes": list(self.reason_codes),
            "status": self.status,
            "timestamp": self.timestamp,
        }

    def get_fingerprint(self) -> str:
        """
        Generate a stable content fingerprint for alert deduplication.
        """
        raw = f"{self.case_id}:{self.alert_triggered}:{self.priority}:{','.join(sorted(self.reason_codes))}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
