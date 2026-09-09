"""
alert_engine.py
===============
Core Alert Engine for MEDHA.

PURPOSE
-------
Consumes risk assessments and context signals generated upstream to determine
whether an alert should be triggered, assigns alert priority, generates non-diagnostic
support messages and actionable Call-to-Actions (CTAs), and produces structured alert payloads.

Also provides an immediate conversational fast-path (`evaluate_conversational_safety`) to trigger
instant alerts on explicit physical safety statements without waiting for async fusion cycles.

DESIGN PRINCIPLES
-----------------
1. Downstream Only: Does NOT calculate a new risk score; purely evaluates upstream risk & context.
2. Transparent Priority Policy: Maps RiskLevel and contextual factors deterministically to priorities.
3. Non-Diagnostic Safety: Generates support-oriented notifications, avoiding medical/clinical claims.
4. Deduplication Ready: Produces deterministic alert fingerprints/IDs and provides deduplication checks.
5. Configurable Wording: Routes and messages can be customized via configuration parameters.
"""

from typing import Dict, List, Any, Optional, Union
import hashlib
from datetime import datetime, timezone

from .schemas import (
    AlertInput,
    AlertOutput,
    AlertPriority,
    AlertType,
    AlertStatus,
    ReasonCode,
    RiskLevel,
    Trend,
    SignalsInput,
    ContextInput,
)

MODALITY_DISTRESS_THRESHOLD = 0.70

# Explicit physical safety keywords for immediate conversational fast-path
EXPLICIT_SAFETY_KEYWORDS = [
    "threatened to kill",
    "threat to kill",
    "in immediate danger",
    "someone is stalking",
    "he has a weapon",
    "she has a weapon",
    "afraid for my life",
    "threat to my life",
    "threatened my life",
    "threatened my family",
    "physical harm",
    "being followed",
    "forced entry",
    "trying to hurt me",
    "trying to attack",
    "he is outside",
    "she is outside",
    "unsafe right now",
    "stalking me",
]


class AlertEngine:
    """
    Deterministic rule-based Alert Engine for MEDHA.
    """

    def __init__(
        self,
        modality_threshold: float = MODALITY_DISTRESS_THRESHOLD,
        custom_templates: Optional[Dict[str, Any]] = None,
    ):
        self.modality_threshold = modality_threshold
        self.custom_templates = custom_templates or {}

    def get_alert(
        self,
        input_data: Union[Dict[str, Any], AlertInput],
        timestamp: Optional[str] = None,
        source: str = "fusion_pipeline",
    ) -> AlertOutput:
        """
        Evaluate risk assessment and context to generate a structured alert.

        :param input_data: Input dict or AlertInput instance.
        :param timestamp: Optional ISO timestamp string (if None, current UTC ISO timestamp is used).
        :param source: Originating source module (default: "fusion_pipeline").
        :return: AlertOutput instance.
        """
        # 1. Parse and validate input
        if isinstance(input_data, dict):
            typed_input = AlertInput.from_dict(input_data)
        elif isinstance(input_data, AlertInput):
            typed_input = input_data
        else:
            raise TypeError(f"Expected dict or AlertInput, got {type(input_data).__name__}")

        # 2. Collect Reason Codes deterministically
        reason_codes = self._collect_reason_codes(typed_input)

        # 3. Determine Alert Trigger, Priority, Type, and Content
        alert_triggered, priority, alert_type, title, message, action, cta = self._evaluate_alert_content(
            typed_input
        )

        # 4. Generate deterministic alert ID based on case_id and trigger signature
        sig_str = f"{typed_input.case_id}:{alert_triggered}:{priority.value}:{alert_type.value}:{','.join(reason_codes)}"
        sig_hash = hashlib.sha256(sig_str.encode("utf-8")).hexdigest()[:8]
        alert_id = f"ALT-{typed_input.case_id}-{sig_hash}"

        # 5. Determine primary reason string
        reason_desc = f"{priority.value} alert generated: {', '.join(reason_codes)}" if reason_codes else f"{priority.value} alert generated."

        # 6. Ensure timestamp
        ts = timestamp if timestamp is not None else datetime.now(timezone.utc).isoformat()

        return AlertOutput(
            alert_id=alert_id,
            case_id=typed_input.case_id,
            alert_triggered=alert_triggered,
            priority=priority.value,
            alert_type=alert_type.value,
            title=title,
            message=message,
            reason=reason_desc,
            source=source,
            recommended_action=action,
            cta=cta,
            reason_codes=reason_codes,
            status=AlertStatus.NEW.value,
            timestamp=ts,
        )

    # Alias for flexibility
    generate_alert = get_alert

    def evaluate_conversational_safety(
        self,
        text: str,
        case_id: str = "UNKNOWN",
        safety_concern_mentioned: Optional[bool] = None,
        timestamp: Optional[str] = None,
    ) -> Optional[AlertOutput]:
        """
        Fast-path safety trigger for explicit conversational statements.

        Evaluates user conversational text or NLP extraction flags immediately
        to detect explicit physical safety threats without waiting for an async fusion cycle.
        Does NOT assign clinical diagnoses or severity scores.

        :param text: Raw user conversational string.
        :param case_id: Victim or case ID.
        :param safety_concern_mentioned: Optional boolean flag from NLP extraction.
        :param timestamp: Optional ISO timestamp string.
        :return: AlertOutput if an immediate safety concern is detected, else None.
        """
        if not text and not safety_concern_mentioned:
            return None

        lowered_text = str(text or "").lower()
        keyword_match = any(kw in lowered_text for kw in EXPLICIT_SAFETY_KEYWORDS)

        if keyword_match or safety_concern_mentioned is True:
            ts = timestamp if timestamp is not None else datetime.now(timezone.utc).isoformat()
            sig_hash = hashlib.sha256(f"{case_id}:CONV_SAFETY:{lowered_text[:30]}".encode("utf-8")).hexdigest()[:8]
            alert_id = f"ALT-{case_id}-IMM-{sig_hash}"

            reason_codes = [
                ReasonCode.THREAT_REPORTED.value,
                ReasonCode.CONVERSATIONAL_SAFETY_CONCERN.value,
            ]

            return AlertOutput(
                alert_id=alert_id,
                case_id=case_id,
                alert_triggered=True,
                priority=AlertPriority.URGENT.value,
                alert_type=AlertType.SAFETY_ESCALATION.value,
                title="Immediate Safety Concern Detected",
                message="An explicit safety concern was mentioned during conversational interaction.",
                reason="Explicit physical safety concern detected in conversational input.",
                source="conversational_safety_trigger",
                recommended_action="Connect with counsellor or safety team for immediate safety assessment.",
                cta="Review Safety Support",
                reason_codes=reason_codes,
                status=AlertStatus.NEW.value,
                timestamp=ts,
            )

        return None

    def _collect_reason_codes(self, data: AlertInput) -> List[str]:
        """
        Collect standardized reason codes based on risk level, trend, context, and signals.
        """
        codes: List[str] = []

        # 1. Risk Level Code
        if data.risk_level == RiskLevel.CRITICAL:
            codes.append(ReasonCode.CRITICAL_RISK.value)
        elif data.risk_level == RiskLevel.HIGH:
            codes.append(ReasonCode.HIGH_RISK.value)
        elif data.risk_level == RiskLevel.MODERATE:
            codes.append(ReasonCode.MODERATE_RISK.value)
        elif data.risk_level == RiskLevel.LOW:
            codes.append(ReasonCode.LOW_RISK.value)

        # 2. Trend Code
        if data.trend == Trend.INCREASING:
            codes.append(ReasonCode.INCREASING_TREND.value)
        elif data.trend == Trend.DECREASING:
            codes.append(ReasonCode.DECREASING_TREND.value)
        elif data.trend == Trend.STABLE:
            codes.append(ReasonCode.STABLE_TREND.value)

        # 3. Context Codes
        ctx = data.context
        if ctx.threat_event:
            codes.append(ReasonCode.THREAT_REPORTED.value)
        if ctx.protection_issue:
            codes.append(ReasonCode.PROTECTION_CONCERN.value)
        if ctx.financial_hardship:
            codes.append(ReasonCode.FINANCIAL_HARDSHIP.value)
        if ctx.rehabilitation_issue:
            codes.append(ReasonCode.REHABILITATION_ISSUE.value)
        if ctx.investigation_delay:
            codes.append(ReasonCode.INVESTIGATION_DELAY.value)
        if ctx.compensation_delay:
            codes.append(ReasonCode.COMPENSATION_DELAY.value)

        # 4. Modality Signals Codes
        sig = data.signals
        if sig.text_distress is not None and sig.text_distress >= self.modality_threshold:
            codes.append(ReasonCode.HIGH_TEXT_DISTRESS.value)
        if sig.voice_distress is not None and sig.voice_distress >= self.modality_threshold:
            codes.append(ReasonCode.HIGH_VOICE_DISTRESS.value)
        if sig.behavioural_risk is not None and sig.behavioural_risk >= self.modality_threshold:
            codes.append(ReasonCode.ELEVATED_BEHAVIOURAL_RISK.value)
        if sig.structured_risk is not None and sig.structured_risk >= self.modality_threshold:
            codes.append(ReasonCode.HIGH_STRUCTURED_RISK.value)
        if sig.temporal_risk is not None and sig.temporal_risk >= self.modality_threshold:
            codes.append(ReasonCode.HIGH_TEMPORAL_RISK.value)

        return codes

    def _evaluate_alert_content(
        self, data: AlertInput
    ) -> tuple[bool, AlertPriority, AlertType, str, str, str, str]:
        """
        Evaluate the priority policy and generate content tuples:
        (alert_triggered, priority, alert_type, title, message, recommended_action, cta)
        """
        level = data.risk_level
        trend = data.trend
        has_threat = data.context.threat_event
        has_protection = data.context.protection_issue
        has_safety_context = has_threat or has_protection

        # CRITICAL
        if level == RiskLevel.CRITICAL:
            if has_safety_context:
                return (
                    True,
                    AlertPriority.IMMEDIATE,
                    AlertType.CRISIS_ESCALATION,
                    "Immediate Safety & Crisis Escalation",
                    "Critical assessment threshold and acute safety concerns require immediate support escalation.",
                    "Escalate immediately to designated supervisor and authorized emergency crisis support.",
                    "Emergency Support Liaison",
                )
            return (
                True,
                AlertPriority.IMMEDIATE,
                AlertType.CRISIS_ESCALATION,
                "Immediate Support Escalation",
                "Critical assessment threshold reached; immediate coordination with designated support personnel is recommended.",
                "Escalate to designated crisis support team or case supervisor immediately.",
                "Emergency Support Liaison",
            )

        # HIGH
        if level == RiskLevel.HIGH:
            if has_safety_context:
                return (
                    True,
                    AlertPriority.URGENT,
                    AlertType.SAFETY_ESCALATION,
                    "High Priority Safety Alert",
                    "High risk assessment accompanied by safety concerns indicates prioritized support is required.",
                    "Connect with a counsellor and review case protection protocols.",
                    "Talk to a Counsellor",
                )
            if trend == Trend.INCREASING:
                return (
                    True,
                    AlertPriority.URGENT,
                    AlertType.SUPPORT_RISK,
                    "Important Support Update",
                    "Recent assessments indicate elevated distress and upward trend where priority support is recommended.",
                    "Connect with a counsellor for follow-up support.",
                    "Talk to a Counsellor",
                )
            # HIGH + STABLE / DECREASING
            return (
                True,
                AlertPriority.PRIORITY,
                AlertType.SUPPORT_RISK,
                "Important Support Update",
                "Recent assessments indicate that additional support may be helpful.",
                "Connect with a counsellor for follow-up support.",
                "Talk to a Counsellor",
            )

        # MODERATE
        if level == RiskLevel.MODERATE:
            if has_safety_context:
                return (
                    True,
                    AlertPriority.URGENT,
                    AlertType.SAFETY_ESCALATION,
                    "Support and Safety Notification",
                    "Moderate risk assessment accompanied by reported safety concerns requires follow-up.",
                    "Review safety support protocols and connect with a support provider.",
                    "Connect with Support",
                )
            if trend == Trend.INCREASING:
                return (
                    True,
                    AlertPriority.PRIORITY,
                    AlertType.SUPPORT_RISK,
                    "Support Update - Increasing Pattern",
                    "Recent assessments indicate an increasing distress trajectory where follow-up support may be helpful.",
                    "Consider connecting with a counsellor or support team for a follow-up.",
                    "Connect with Support",
                )
            # MODERATE + STABLE / DECREASING
            return (
                True,
                AlertPriority.ATTENTION,
                AlertType.SUPPORT_NOTIFICATION,
                "Support Check-In",
                "Recent assessments suggest that supportive resources and routine check-ins may be helpful.",
                "Explore available support resources or schedule a routine check-in.",
                "Explore Support Options",
            )

        # LOW
        if has_safety_context:
            return (
                True,
                AlertPriority.URGENT,
                AlertType.SAFETY_ESCALATION,
                "Safety Context Alert",
                "Although baseline risk is low, a safety or protection concern was noted in the case context.",
                "Review safety precautions and verify support needs.",
                "Review Safety Support",
            )

        # Normal LOW (STABLE or DECREASING)
        return (
            False,
            AlertPriority.ROUTINE,
            AlertType.MONITORING,
            "Routine Monitoring",
            "Current assessments indicate routine support status.",
            "Maintain regular check-in schedule.",
            "View Wellness Resources",
        )


def is_duplicate_alert(
    previous_alert: Union[Dict[str, Any], AlertOutput],
    current_alert: Union[Dict[str, Any], AlertOutput],
) -> bool:
    """
    Determine if a newly generated alert is a duplicate of a previous active alert.

    Compares case_id, alert_triggered status, priority, and sorted reason codes.
    """
    p_dict = previous_alert.to_dict() if isinstance(previous_alert, AlertOutput) else previous_alert
    c_dict = current_alert.to_dict() if isinstance(current_alert, AlertOutput) else current_alert

    if p_dict.get("case_id") != c_dict.get("case_id"):
        return False
    if p_dict.get("alert_triggered") != c_dict.get("alert_triggered"):
        return False
    if p_dict.get("priority") != c_dict.get("priority"):
        return False

    p_reasons = sorted(p_dict.get("reason_codes", []))
    c_reasons = sorted(c_dict.get("reason_codes", []))
    return p_reasons == c_reasons


def evaluate_conversational_safety(
    text: str,
    case_id: str = "UNKNOWN",
    safety_concern_mentioned: Optional[bool] = None,
    timestamp: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Convenience function returning conversational safety alert as a plain dict (or None).
    """
    engine = AlertEngine()
    alert = engine.evaluate_conversational_safety(
        text=text,
        case_id=case_id,
        safety_concern_mentioned=safety_concern_mentioned,
        timestamp=timestamp,
    )
    return alert.to_dict() if alert else None


def get_alert(
    input_data: Union[Dict[str, Any], AlertInput],
    timestamp: Optional[str] = None,
    source: str = "fusion_pipeline",
    modality_threshold: float = MODALITY_DISTRESS_THRESHOLD,
) -> Dict[str, Any]:
    """
    Convenience function returning alert output as a plain dictionary.
    """
    engine = AlertEngine(modality_threshold=modality_threshold)
    return engine.get_alert(input_data, timestamp=timestamp, source=source).to_dict()
