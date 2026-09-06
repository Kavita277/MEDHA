"""
recommendation_engine.py
========================
Core Recommendation + Intervention Engine for MEDHA.

PURPOSE
-------
Consumes risk scores, trend trajectories, sub-signals, and case context
(from the caller / future fusion module) and produces deterministic, explainable,
and safety-guarded intervention recommendations along with tailored self-help resources.

DESIGN PRINCIPLES
-----------------
- 100% Rule-based and Deterministic: Zero internal ML training or predicting.
- Explainable: Every recommendation contains an explicit rationale.
- Non-Diagnostic: Strict safety adherence; phrasing uses referral and assessment language.
- Standalone & Decoupled: Zero dependency on ongoing fusion module internals.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .schemas import (
    RecommendationEngineInput,
    RecommendationEngineOutput,
    Recommendation,
    SelfHelpResource,
    Priority,
)
from .rules import (
    evaluate_base_risk_rules,
    evaluate_trend_rules,
    evaluate_context_rules,
    select_self_help_resources,
    validate_safety_phrasing,
)

_PRIORITY_ORDER = {
    Priority.IMMEDIATE.value: 1,
    Priority.URGENT.value: 2,
    Priority.PRIORITY.value: 3,
    Priority.INCREASED.value: 4,
    Priority.ROUTINE.value: 5,
}


class RecommendationEngine:
    """
    Deterministic rule-based recommendation and intervention engine.
    """

    def __init__(self, resources_path: Optional[str] = None):
        """
        Initialize the recommendation engine and load self-help resource catalog.
        """
        self.resources_path = resources_path or self._resolve_default_resources_path()
        self.resource_catalog = self._load_resources(self.resources_path)

    @staticmethod
    def _resolve_default_resources_path() -> str:
        """
        Locate default resources.json or medha_resources.json in the same folder.
        """
        current_dir = Path(__file__).resolve().parent
        res_json = current_dir / "resources.json"
        if res_json.exists():
            return str(res_json)
        medha_res = current_dir / "medha_resources.json"
        if medha_res.exists():
            return str(medha_res)
        return str(res_json)

    @staticmethod
    def _load_resources(path: str) -> List[Dict[str, Any]]:
        """
        Load resource library from JSON file.
        """
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_recommendations(
        self,
        input_data: Union[Dict[str, Any], RecommendationEngineInput],
    ) -> RecommendationEngineOutput:
        """
        Generate deterministic intervention recommendations and select self-help resources.

        :param input_data: Input dict or RecommendationEngineInput instance.
        :return: RecommendationEngineOutput with structured recommendations and self_help items.
        """
        # 1. Parse and validate input
        if isinstance(input_data, dict):
            typed_input = RecommendationEngineInput.from_dict(input_data)
        elif isinstance(input_data, RecommendationEngineInput):
            typed_input = input_data
        else:
            raise TypeError(
                f"Expected dict or RecommendationEngineInput, got {type(input_data).__name__}"
            )

        # 2. Evaluate rule sets
        recs: List[Recommendation] = []
        recs.extend(evaluate_base_risk_rules(typed_input))
        recs.extend(evaluate_trend_rules(typed_input))
        recs.extend(evaluate_context_rules(typed_input))

        # 3. Deduplicate recommendations by ID while preserving priority
        seen_ids = set()
        deduped_recs: List[Recommendation] = []
        for r in recs:
            if r.id not in seen_ids:
                # Safety guardrail check
                if not validate_safety_phrasing(r.action) or not validate_safety_phrasing(r.reason):
                    raise ValueError(f"Safety guardrail violation in recommendation text: {r.id}")
                deduped_recs.append(r)
                seen_ids.add(r.id)

        # 4. Sort recommendations deterministically by priority rank
        deduped_recs.sort(key=lambda item: _PRIORITY_ORDER.get(item.priority, 99))

        # 5. Select matching self-help resources
        self_help = select_self_help_resources(typed_input, self.resource_catalog)

        # 6. Construct and return output
        return RecommendationEngineOutput(
            case_id=typed_input.case_id,
            risk_level=typed_input.risk_level.value,
            recommendations=deduped_recs,
            self_help=self_help,
        )

    # Alias for flexibility
    generate_recommendations = get_recommendations


def get_recommendations(
    input_data: Union[Dict[str, Any], RecommendationEngineInput],
    resources_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to get recommendation output as a plain dictionary.
    """
    engine = RecommendationEngine(resources_path=resources_path)
    return engine.get_recommendations(input_data).to_dict()
