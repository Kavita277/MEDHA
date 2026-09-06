"""
rules.py
========
Deterministic, explainable rule set for MEDHA's Recommendation + Intervention Engine.

PURPOSE
-------
Evaluates risk levels, trend trajectories, sub-signals, case context, and
QuestionEngine intents to produce structured intervention recommendations
and map relevant self-help resources.

SAFETY PRINCIPLES
-----------------
1. Recommendations are phrased strictly as referrals, suggestions, or assessments,
   NEVER as autonomous medical/psychiatric diagnoses or treatment mandates.
2. Complete determinism: identical inputs produce identical outputs with full explainability.
3. No ML prediction is conducted here; rules purely consume caller-provided signals.
"""

from typing import List, Dict, Any, Set
from .schemas import (
    RecommendationEngineInput,
    Recommendation,
    SelfHelpResource,
    RiskLevel,
    Trend,
    Priority,
    Category,
    Intent,
)

# Forbidden phrases that must never appear in recommendations (Safety Guardrail)
FORBIDDEN_DIAGNOSTIC_TERMS = [
    "is clinically",
    "suffers from",
    "has diagnosed",
    "requires medical treatment",
    "is diagnosed",
    "has major depressive",
    "victim is mentally",
    "prescribe",
]


def evaluate_base_risk_rules(input_data: RecommendationEngineInput) -> List[Recommendation]:
    """
    Generate core recommendations based strictly on the fused risk level.
    """
    recs: List[Recommendation] = []
    level = input_data.risk_level

    if level == RiskLevel.LOW:
        recs.append(
            Recommendation(
                id="REC-MON-001",
                category=Category.MONITORING.value,
                priority=Priority.ROUTINE.value,
                reason=f"Case assessed at LOW risk level (score: {input_data.fused_risk_score:.2f}).",
                action="Maintain routine safety and wellness monitoring schedule.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-SH-001",
                category=Category.COUNSELLING.value,
                priority=Priority.ROUTINE.value,
                reason="Supportive wellness self-management recommended for low-risk profile.",
                action="Provide access to self-help wellness and stress-regulation resources.",
            )
        )

    elif level == RiskLevel.MODERATE:
        recs.append(
            Recommendation(
                id="REC-COUNSEL-001",
                category=Category.COUNSELLING.value,
                priority=Priority.INCREASED.value,
                reason=f"Case assessed at MODERATE risk level (score: {input_data.fused_risk_score:.2f}).",
                action="Consider scheduled counsellor follow-up session within the standard review window.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-MON-002",
                category=Category.MONITORING.value,
                priority=Priority.INCREASED.value,
                reason="Moderate risk indicators suggest closer observational cadence.",
                action="Increase monitoring frequency and schedule closer check-in intervals.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-SH-002",
                category=Category.COUNSELLING.value,
                priority=Priority.ROUTINE.value,
                reason="Coping and emotional stabilization materials indicated for moderate distress.",
                action="Provide structured emotional de-escalation and coping resources.",
            )
        )

    elif level == RiskLevel.HIGH:
        recs.append(
            Recommendation(
                id="REC-COUNSEL-002",
                category=Category.COUNSELLING.value,
                priority=Priority.PRIORITY.value,
                reason=f"Case assessed at HIGH risk level (score: {input_data.fused_risk_score:.2f}).",
                action="Consider priority counsellor follow-up session within 24 to 48 hours.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-INTV-001",
                category=Category.INTERVENTION.value,
                priority=Priority.PRIORITY.value,
                reason="Elevated composite risk warrants multi-disciplinary support planning.",
                action="Recommend multi-disciplinary case review and tailored support planning.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-MON-003",
                category=Category.MONITORING.value,
                priority=Priority.PRIORITY.value,
                reason="High risk classification necessitates enhanced monitoring vigilance.",
                action="Initiate active high-frequency case monitoring and check-ins.",
            )
        )

    elif level == RiskLevel.CRITICAL:
        recs.append(
            Recommendation(
                id="REC-ESC-001",
                category=Category.ESCALATION.value,
                priority=Priority.IMMEDIATE.value,
                reason=f"CRITICAL risk level flagged (score: {input_data.fused_risk_score:.2f}) requiring urgent response.",
                action="Recommend immediate escalation to authorized supervisor and designated crisis response team.",
            )
        )
        recs.append(
            Recommendation(
                id="REC-PROF-001",
                category=Category.INTERVENTION.value,
                priority=Priority.URGENT.value,
                reason="Critical risk threshold reached; urgent professional assessment indicated.",
                action="Recommend urgent follow-up by qualified professional or authorized support provider.",
            )
        )

    return recs


def evaluate_trend_rules(input_data: RecommendationEngineInput) -> List[Recommendation]:
    """
    Evaluate temporal trend trajectory.
    """
    recs: List[Recommendation] = []
    
    if input_data.trend == Trend.INCREASING:
        recs.append(
            Recommendation(
                id="REC-TREND-INC",
                category=Category.MONITORING.value,
                priority=Priority.PRIORITY.value,
                reason="Upward distress trajectory detected across sequential evaluations.",
                action="Schedule expedited priority follow-up due to increasing distress trend.",
            )
        )
    return recs


def evaluate_context_rules(input_data: RecommendationEngineInput) -> List[Recommendation]:
    """
    Evaluate domain-specific contextual indicators (legal, financial, protection, rehab).
    """
    recs: List[Recommendation] = []
    ctx = input_data.context

    # Threat event
    if ctx.threat_event:
        recs.append(
            Recommendation(
                id="REC-CTX-THREAT",
                category=Category.PROTECTION.value,
                priority=Priority.URGENT.value,
                reason="Active threat event reported in case context.",
                action="Assess whether immediate protection support, safety planning, and security measures are required.",
            )
        )

    # Protection issue (if distinct from or combined with threat event)
    if ctx.protection_issue and not ctx.threat_event:
        recs.append(
            Recommendation(
                id="REC-CTX-PROT",
                category=Category.PROTECTION.value,
                priority=Priority.PRIORITY.value,
                reason="Protection concern identified in case context.",
                action="Assess whether appropriate protection support and safe contact protocols are required.",
            )
        )

    # Financial hardship
    if ctx.financial_hardship:
        recs.append(
            Recommendation(
                id="REC-CTX-FIN",
                category=Category.FINANCIAL_SUPPORT.value,
                priority=Priority.PRIORITY.value if input_data.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) else Priority.ROUTINE.value,
                reason="Financial hardship identified in case context.",
                action="Provide information on available victim compensation schemes, relief grants, and financial assistance programs.",
            )
        )

    # Compensation delay
    if ctx.compensation_delay and not ctx.financial_hardship:
        recs.append(
            Recommendation(
                id="REC-CTX-COMP",
                category=Category.FINANCIAL_SUPPORT.value,
                priority=Priority.ROUTINE.value,
                reason="Delay in victim compensation processing reported.",
                action="Coordinate with victim compensation liaison officer to review application status.",
            )
        )

    # Investigation delay
    if ctx.investigation_delay:
        recs.append(
            Recommendation(
                id="REC-CTX-LEGAL",
                category=Category.LEGAL_SUPPORT.value,
                priority=Priority.ROUTINE.value,
                reason="Investigation or procedural case delay reported in context.",
                action="Refer to legal aid advocate or case liaison officer for procedural status review.",
            )
        )

    # Rehabilitation issue
    if ctx.rehabilitation_issue:
        recs.append(
            Recommendation(
                id="REC-CTX-REHAB",
                category=Category.REHABILITATION.value,
                priority=Priority.ROUTINE.value,
                reason="Rehabilitation or community reintegration barrier identified in context.",
                action="Coordinate referral to accredited community rehabilitation and social reintegration services.",
            )
        )

    return recs


def select_self_help_resources(
    input_data: RecommendationEngineInput,
    catalog: List[Dict[str, Any]],
) -> List[SelfHelpResource]:
    """
    Select relevant self-help and support resources matching the case profile.
    Deterministic selection based on risk level, active context tags, and QuestionEngine intents.
    """
    # Active tags to look for in resources
    target_tags: Set[str] = set()

    # QuestionEngine intent tags (if supplied)
    if input_data.intent is not None:
        if isinstance(input_data.intent, (list, tuple, set)):
            for item in input_data.intent:
                val = item.value if isinstance(item, Intent) else str(item).lower()
                target_tags.add(val)
        elif isinstance(input_data.intent, Intent):
            target_tags.add(input_data.intent.value)
        else:
            target_tags.add(str(input_data.intent).lower())

    # Risk level mapping
    risk_str = input_data.risk_level.value.lower()
    target_tags.add(risk_str)

    if input_data.risk_level in (RiskLevel.LOW, RiskLevel.MODERATE):
        target_tags.add("wellness")
        target_tags.add("routine")

    if input_data.risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH):
        target_tags.add("coping")

    if input_data.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        target_tags.add("crisis")

    if input_data.trend == Trend.INCREASING:
        target_tags.add("increasing_trend")
        target_tags.add("distress")

    ctx = input_data.context
    if ctx.threat_event or ctx.protection_issue:
        target_tags.add("threat_event")
        target_tags.add("protection_issue")
        target_tags.add("protection")

    if ctx.investigation_delay:
        target_tags.add("investigation_delay")
        target_tags.add("legal_support")

    if ctx.financial_hardship or ctx.compensation_delay:
        target_tags.add("financial_hardship")
        target_tags.add("compensation_delay")
        target_tags.add("financial_support")

    if ctx.rehabilitation_issue:
        target_tags.add("rehabilitation_issue")
        target_tags.add("rehabilitation")

    selected: List[SelfHelpResource] = []
    seen_ids: Set[str] = set()

    for item in catalog:
        item_id = item.get("id", "")
        if item_id in seen_ids:
            continue

        item_tags = set(item.get("tags", []))
        if item_tags.intersection(target_tags):
            selected.append(
                SelfHelpResource(
                    id=item_id,
                    type=item.get("type", "guide"),
                    title=item.get("title", ""),
                    category=item.get("category", "general"),
                    description=item.get("description", ""),
                )
            )
            seen_ids.add(item_id)

    return selected


def validate_safety_phrasing(text: str) -> bool:
    """
    Safety guardrail check to verify text contains no diagnostic / clinical assertion terms.
    Returns True if safe, False if violations found.
    """
    lower = text.lower()
    for term in FORBIDDEN_DIAGNOSTIC_TERMS:
        if term in lower:
            return False
    return True
