"""
explainability_engine.py
========================
Core Explainability Engine for MEDHA.

PURPOSE
-------
Converts upstream model/fusion signals (risk scores, trajectories, modality
sub-signals, and case context) into simple, non-diagnostic, deterministic explanations
for end-users and care teams.

DESIGN PRINCIPLES
-----------------
1. 100% Deterministic: Identical inputs produce identical structured explanations.
2. Non-Diagnostic Safety: Explanations are strictly phrased as support indicators
   and observational summaries, NEVER as medical/psychiatric diagnoses.
3. Decoupled & Modular: Works independently of fusion module internals and handles
   missing optional signals gracefully.
4. Preserves Structured Factor Breakdown: Formats factors by category (trend, voice,
   text, behaviour, structured, temporal, context, activity) for transparent viewing.
"""

from typing import Dict, List, Any, Optional, Union
from .schemas import (
    ExplainabilityInput,
    ExplainabilityOutput,
    Factor,
    FactorType,
    RiskLevel,
    Trend,
    SignalsInput,
    ContextInput,
    RecentActivityInput,
)

# Safety Guardrail: Forbidden diagnostic/clinical assertion terms
FORBIDDEN_DIAGNOSTIC_TERMS = [
    "you have depression",
    "you are clinically",
    "the model diagnosed",
    "is diagnosed with",
    "suffers from",
    "requires medical treatment",
    "this factor caused",
    "prescribe",
    "psychiatric disorder",
]

# Modality signal significance threshold (signals at or above this are flagged as significant contributors)
DEFAULT_SIGNAL_THRESHOLD = 0.60


def validate_safety_phrasing(text: str) -> bool:
    """
    Validate that text contains no forbidden clinical/diagnostic terms.
    """
    lowered = text.lower()
    for term in FORBIDDEN_DIAGNOSTIC_TERMS:
        if term in lowered:
            return False
    return True


class ExplainabilityEngine:
    """
    Deterministic, rule-based Explainability Engine for MEDHA risk and support assessments.
    """

    def __init__(self, signal_threshold: float = DEFAULT_SIGNAL_THRESHOLD):
        self.signal_threshold = signal_threshold

    def get_explanation(
        self,
        input_data: Union[Dict[str, Any], ExplainabilityInput],
    ) -> ExplainabilityOutput:
        """
        Generate a deterministic, non-diagnostic explanation from fused assessment data.

        :param input_data: Input dictionary or ExplainabilityInput instance.
        :return: ExplainabilityOutput instance containing summary, factor list, trend explanation, and disclaimer.
        """
        # 1. Parse and validate input
        if isinstance(input_data, dict):
            typed_input = ExplainabilityInput.from_dict(input_data)
        elif isinstance(input_data, ExplainabilityInput):
            typed_input = input_data
        else:
            raise TypeError(
                f"Expected dict or ExplainabilityInput, got {type(input_data).__name__}"
            )

        # 2. Build non-diagnostic summary
        summary = self._build_summary(typed_input)

        # 3. Build contributing factors
        factors: List[Factor] = []

        # 3a. Trend factor
        trend_factor = self._build_trend_factor(typed_input)
        if trend_factor:
            factors.append(trend_factor)

        # 3b. Modality signals factors
        modality_factors = self._build_modality_factors(typed_input)
        factors.extend(modality_factors)

        # 3c. Contextual factors
        context_factors = self._build_context_factors(typed_input)
        factors.extend(context_factors)

        # 3d. Recent activity factor
        activity_factor = self._build_activity_factor(typed_input)
        if activity_factor:
            factors.append(activity_factor)

        # 4. Build trend explanation
        trend_explanation = self._build_trend_explanation(typed_input)

        # 5. Non-diagnostic disclaimer
        disclaimer = "This is a support-oriented explanation and is not a medical diagnosis."

        # 6. Safety validation
        for f in factors:
            if not validate_safety_phrasing(f.description) or not validate_safety_phrasing(f.factor):
                raise ValueError(f"Safety guardrail violation in factor phrasing: {f.factor}")
        if not validate_safety_phrasing(summary) or not validate_safety_phrasing(trend_explanation):
            raise ValueError("Safety guardrail violation in summary or trend explanation.")

        return ExplainabilityOutput(
            case_id=typed_input.case_id,
            summary=summary,
            factors=factors,
            trend_explanation=trend_explanation,
            disclaimer=disclaimer,
            risk_level=typed_input.risk_level.value,
        )

    # Alias for flexibility
    generate_explanation = get_explanation

    def _build_summary(self, data: ExplainabilityInput) -> str:
        """
        Generate high-level, non-diagnostic support summary based on risk level and context.
        """
        level = data.risk_level
        has_threat = data.context.threat_event or data.context.protection_issue

        if level == RiskLevel.CRITICAL:
            if has_threat:
                return "Recent assessments and reported safety concerns indicate that immediate support and safety coordination are recommended."
            return "Recent assessments indicate that immediate support and coordination are recommended."

        if level == RiskLevel.HIGH:
            if data.trend == Trend.INCREASING:
                return "Recent check-ins and increasing distress patterns indicate that prioritized counsellor support is recommended."
            return "Recent check-ins indicate that additional support may be helpful."

        if level == RiskLevel.MODERATE:
            if data.trend == Trend.INCREASING:
                return "Recent check-ins indicate an increasing pattern where follow-up support may be helpful."
            return "Recent check-ins indicate that supportive resources and routine check-ins may be beneficial."

        # LOW
        if data.trend == Trend.DECREASING:
            return "Recent check-ins indicate a positive and stabilizing trend."
        return "Recent responses suggest that current support levels are stable."

    def _build_trend_factor(self, data: ExplainabilityInput) -> Optional[Factor]:
        """
        Explain the longitudinal trend trajectory.
        """
        if data.trend == Trend.INCREASING:
            return Factor(
                factor="Recent check-ins",
                description="Recent responses indicate increased distress compared with earlier check-ins.",
                type=FactorType.TREND.value,
            )
        elif data.trend == Trend.DECREASING:
            return Factor(
                factor="Recent check-ins",
                description="Recent responses show a decreasing distress pattern over time.",
                type=FactorType.TREND.value,
            )
        elif data.trend == Trend.STABLE:
            # For LOW risk stable, a stable factor can be noted if requested or omitted if low
            if data.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                return Factor(
                    factor="Trajectory stability",
                    description="Distress levels have remained consistently elevated across sequential evaluations.",
                    type=FactorType.TREND.value,
                )
        return None

    def _build_modality_factors(self, data: ExplainabilityInput) -> List[Factor]:
        """
        Generate factors from individual modality signals that exceed the threshold.
        """
        factors: List[Factor] = []
        sig = data.signals

        # Voice distress
        if sig.voice_distress is not None and sig.voice_distress >= self.signal_threshold:
            factors.append(
                Factor(
                    factor="Voice interaction",
                    description="Recent voice interaction contributed to the overall assessment.",
                    type=FactorType.VOICE.value,
                )
            )

        # Text distress
        if sig.text_distress is not None and sig.text_distress >= self.signal_threshold:
            factors.append(
                Factor(
                    factor="Text interaction",
                    description="Language observed in recent check-ins contributed to the overall assessment.",
                    type=FactorType.TEXT.value,
                )
            )

        # Temporal risk
        if sig.temporal_risk is not None and sig.temporal_risk >= self.signal_threshold:
            factors.append(
                Factor(
                    factor="Temporal pattern",
                    description="Sequential changes observed over time contributed to the assessment.",
                    type=FactorType.TEMPORAL.value,
                )
            )

        # Behavioural risk
        if sig.behavioural_risk is not None and sig.behavioural_risk >= self.signal_threshold:
            factors.append(
                Factor(
                    factor="Interaction patterns",
                    description="Interaction frequency and response timing patterns were noted during recent check-ins.",
                    type=FactorType.BEHAVIOUR.value,
                )
            )

        # Structured risk
        if sig.structured_risk is not None and sig.structured_risk >= self.signal_threshold:
            factors.append(
                Factor(
                    factor="Baseline intake profile",
                    description="Baseline case context and intake profile contributed to the assessment.",
                    type=FactorType.STRUCTURED.value,
                )
            )

        return factors

    def _build_context_factors(self, data: ExplainabilityInput) -> List[Factor]:
        """
        Generate factors from explicit contextual flags.
        """
        factors: List[Factor] = []
        ctx = data.context

        if ctx.threat_event:
            factors.append(
                Factor(
                    factor="Safety concerns",
                    description="A safety-related concern was reported in the case context.",
                    type=FactorType.CONTEXT.value,
                )
            )

        if ctx.protection_issue:
            factors.append(
                Factor(
                    factor="Protection needs",
                    description="A protection-related concern was identified in the case profile.",
                    type=FactorType.CONTEXT.value,
                )
            )

        if ctx.financial_hardship:
            factors.append(
                Factor(
                    factor="Financial hardship",
                    description="Financial strain or hardship was reported in the case context.",
                    type=FactorType.CONTEXT.value,
                )
            )

        if ctx.rehabilitation_issue:
            factors.append(
                Factor(
                    factor="Rehabilitation needs",
                    description="Rehabilitation or medical recovery concerns were noted in the case context.",
                    type=FactorType.CONTEXT.value,
                )
            )

        if ctx.investigation_delay:
            factors.append(
                Factor(
                    factor="Investigation timeline",
                    description="Investigation delays or procedural timeline concerns were noted in the case context.",
                    type=FactorType.CONTEXT.value,
                )
            )

        if ctx.compensation_delay:
            factors.append(
                Factor(
                    factor="Compensation status",
                    description="Compensation processing delays were reported in the case context.",
                    type=FactorType.CONTEXT.value,
                )
            )

        return factors

    def _build_activity_factor(self, data: ExplainabilityInput) -> Optional[Factor]:
        """
        Generate factor for recent user activity if provided.
        """
        if not data.recent_activity:
            return None

        act = data.recent_activity
        total_interactions = (
            act.checkins + act.journal_entries + act.voice_interactions + act.text_interactions
        )
        if total_interactions > 0:
            details = []
            if act.checkins > 0:
                details.append(f"{act.checkins} check-in{'s' if act.checkins > 1 else ''}")
            if act.journal_entries > 0:
                details.append(f"{act.journal_entries} journal entr{'ies' if act.journal_entries > 1 else 'y'}")
            if act.voice_interactions > 0:
                details.append(f"{act.voice_interactions} voice interaction{'s' if act.voice_interactions > 1 else ''}")
            if act.text_interactions > 0:
                details.append(f"{act.text_interactions} text interaction{'s' if act.text_interactions > 1 else ''}")

            desc = f"Recorded activity includes {', '.join(details)}."
            return Factor(
                factor="Recent engagement",
                description=desc,
                type=FactorType.ACTIVITY.value,
            )
        return None

    def _build_trend_explanation(self, data: ExplainabilityInput) -> str:
        """
        Generate deterministic short trend explanation.
        """
        if data.trend == Trend.INCREASING:
            return "The recent pattern has been increasing."
        elif data.trend == Trend.DECREASING:
            return "The recent pattern has been decreasing."
        else:
            return "The recent pattern has been stable."


def get_explanation(
    input_data: Union[Dict[str, Any], ExplainabilityInput],
    signal_threshold: float = DEFAULT_SIGNAL_THRESHOLD,
) -> Dict[str, Any]:
    """
    Convenience function returning explanation as a plain dictionary.
    """
    engine = ExplainabilityEngine(signal_threshold=signal_threshold)
    return engine.get_explanation(input_data).to_dict()
