"""
test_recommendations.py
=======================
Comprehensive test suite for MEDHA Recommendation + Intervention Engine.

Verifies:
1. Scenario 1: LOW + stable
2. Scenario 2: MODERATE + increasing trend
3. Scenario 3: HIGH + threat event
4. Scenario 4: HIGH + financial hardship
5. Scenario 5: HIGH + rehabilitation issue
6. Scenario 6: CRITICAL + protection concern
7. Scenario 7: Multiple simultaneous risk/context factors
8. Intent 1: safety_support
9. Intent 2: event_related_stress
10. Intent 3: sleep_functioning
11. Intent 4: social_emotional_support
12. Intent 5: general_wellbeing
13. Safety Guardrails: Phrased as recommendations/referrals, not diagnoses.
14. Determinism: Identical inputs yield 100% identical outputs.
15. Schema and Catalog Integrity.
"""

import unittest
import json
import os
import sys

# Ensure package can be imported directly when running standalone or via pytest
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from recommendation_engine.recommendation_engine import (
    RecommendationEngine,
    get_recommendations,
)
from recommendation_engine.schemas import (
    RecommendationEngineInput,
    RiskLevel,
    Trend,
    Intent,
    SignalsInput,
    ContextInput,
)
from recommendation_engine.rules import (
    FORBIDDEN_DIAGNOSTIC_TERMS,
    validate_safety_phrasing,
)


class TestRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RecommendationEngine()

    def test_scenario_1_low_stable(self):
        """
        Scenario 1: LOW risk + STABLE trend
        Expected: Routine monitoring and wellness self-help resources.
        """
        payload = {
            "case_id": "CASE-LOW-01",
            "fused_risk_score": 0.15,
            "risk_level": "LOW",
            "trend": "STABLE",
            "signals": {
                "text_distress": 0.1,
                "voice_distress": 0.2,
                "behavioural_risk": 0.1,
                "structured_risk": 0.15,
                "temporal_risk": 0.1,
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": False,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
        }

        output = self.engine.get_recommendations(payload)
        self.assertEqual(output.case_id, "CASE-LOW-01")
        self.assertEqual(output.risk_level, "LOW")

        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-MON-001", rec_ids)
        self.assertIn("REC-SH-001", rec_ids)
        
        # Verify monitoring priority is ROUTINE
        mon_rec = next(r for r in output.recommendations if r.id == "REC-MON-001")
        self.assertEqual(mon_rec.priority, "ROUTINE")
        self.assertIn("routine", mon_rec.action.lower())

        # Verify self-help resources included
        sh_categories = [s.category for s in output.self_help]
        self.assertIn("wellness", sh_categories)

    def test_scenario_2_moderate_increasing_trend(self):
        """
        Scenario 2: MODERATE risk + INCREASING trend
        Expected: Counsellor follow-up, increased monitoring, coping resources,
                  and expedited priority follow-up due to trend.
        """
        payload = {
            "case_id": "CASE-MOD-02",
            "fused_risk_score": 0.45,
            "risk_level": "MODERATE",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.4,
                "voice_distress": 0.5,
                "behavioural_risk": 0.45,
                "structured_risk": 0.35,
                "temporal_risk": 0.6,
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": False,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
        }

        output = self.engine.get_recommendations(payload)
        self.assertEqual(output.risk_level, "MODERATE")

        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-COUNSEL-001", rec_ids)
        self.assertIn("REC-MON-002", rec_ids)
        self.assertIn("REC-TREND-INC", rec_ids)

        # Increasing trend should trigger expedited follow-up
        trend_rec = next(r for r in output.recommendations if r.id == "REC-TREND-INC")
        self.assertEqual(trend_rec.priority, "PRIORITY")
        self.assertIn("increasing distress trend", trend_rec.action.lower())

        # Self-help should include coping/distress tools
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-COP-01", sh_ids)

    def test_scenario_3_high_threat_event(self):
        """
        Scenario 3: HIGH risk + threat event
        Expected: Priority counsellor follow-up, intervention recommendation,
                  protection assessment, safety planning resources.
        """
        payload = {
            "case_id": "CASE-HIGH-03",
            "fused_risk_score": 0.72,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "signals": {
                "text_distress": 0.7,
                "voice_distress": 0.65,
                "behavioural_risk": 0.75,
                "structured_risk": 0.7,
                "temporal_risk": 0.6,
            },
            "context": {
                "threat_event": True,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": False,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
        }

        output = self.engine.get_recommendations(payload)
        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-COUNSEL-002", rec_ids)
        self.assertIn("REC-INTV-001", rec_ids)
        self.assertIn("REC-CTX-THREAT", rec_ids)

        # Protection rec should have URGENT priority
        threat_rec = next(r for r in output.recommendations if r.id == "REC-CTX-THREAT")
        self.assertEqual(threat_rec.priority, "URGENT")
        self.assertEqual(threat_rec.category, "protection")
        self.assertIn("Assess whether", threat_rec.action)

        # Self-help should include safety planning guide
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-PROT-01", sh_ids)

    def test_scenario_4_high_financial_hardship(self):
        """
        Scenario 4: HIGH risk + financial hardship
        Expected: High risk clinical/counsellor recommendations + financial assistance guidance.
        """
        payload = {
            "case_id": "CASE-HIGH-04",
            "fused_risk_score": 0.68,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "signals": {
                "text_distress": 0.65,
                "voice_distress": 0.6,
                "behavioural_risk": 0.7,
                "structured_risk": 0.65,
                "temporal_risk": 0.55,
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": True,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
        }

        output = self.engine.get_recommendations(payload)
        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-COUNSEL-002", rec_ids)
        self.assertIn("REC-CTX-FIN", rec_ids)

        fin_rec = next(r for r in output.recommendations if r.id == "REC-CTX-FIN")
        self.assertEqual(fin_rec.category, "financial_support")
        self.assertIn("compensation", fin_rec.action.lower())

        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-FIN-01", sh_ids)

    def test_scenario_5_high_rehabilitation_issue(self):
        """
        Scenario 5: HIGH risk + rehabilitation issue
        Expected: Priority counsellor review + rehabilitation support coordination & resources.
        """
        payload = {
            "case_id": "CASE-HIGH-05",
            "fused_risk_score": 0.69,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "signals": {
                "text_distress": 0.7,
                "voice_distress": 0.6,
                "behavioural_risk": 0.65,
                "structured_risk": 0.68,
                "temporal_risk": 0.5,
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": False,
                "rehabilitation_issue": True,
                "protection_issue": False,
            },
        }

        output = self.engine.get_recommendations(payload)
        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-COUNSEL-002", rec_ids)
        self.assertIn("REC-CTX-REHAB", rec_ids)

        rehab_rec = next(r for r in output.recommendations if r.id == "REC-CTX-REHAB")
        self.assertEqual(rehab_rec.category, "rehabilitation")
        self.assertIn("rehabilitation", rehab_rec.action.lower())

        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-REHAB-01", sh_ids)

    def test_scenario_6_critical_protection_concern(self):
        """
        Scenario 6: CRITICAL risk + protection concern
        Expected: Immediate escalation recommendation, urgent professional assessment,
                  protection support referral, crisis helpline resources.
        """
        payload = {
            "case_id": "CASE-CRIT-06",
            "fused_risk_score": 0.92,
            "risk_level": "CRITICAL",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.9,
                "voice_distress": 0.88,
                "behavioural_risk": 0.95,
                "structured_risk": 0.85,
                "temporal_risk": 0.9,
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": False,
                "rehabilitation_issue": False,
                "protection_issue": True,
            },
        }

        output = self.engine.get_recommendations(payload)
        self.assertEqual(output.risk_level, "CRITICAL")

        rec_ids = [r.id for r in output.recommendations]
        self.assertIn("REC-ESC-001", rec_ids)
        self.assertIn("REC-PROF-001", rec_ids)
        self.assertIn("REC-CTX-PROT", rec_ids)

        # Escalation is top priority (IMMEDIATE)
        top_rec = output.recommendations[0]
        self.assertEqual(top_rec.priority, "IMMEDIATE")
        self.assertEqual(top_rec.category, "escalation")

        # Crisis support resources included
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-CRISIS-01", sh_ids)
        self.assertIn("SH-PROT-01", sh_ids)

    def test_scenario_7_multiple_simultaneous_factors(self):
        """
        Scenario 7: Multiple simultaneous risk and context factors
        (CRITICAL + INCREASING + Threat + Investigation Delay + Financial Hardship + Rehab Issue)
        Expected: All matching recommendations generated, sorted by priority (IMMEDIATE -> URGENT -> PRIORITY -> ROUTINE).
        """
        payload = {
            "case_id": "CASE-MULTI-07",
            "fused_risk_score": 0.95,
            "risk_level": "CRITICAL",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.92,
                "voice_distress": 0.91,
                "behavioural_risk": 0.88,
                "structured_risk": 0.94,
                "temporal_risk": 0.89,
            },
            "context": {
                "threat_event": True,
                "investigation_delay": True,
                "compensation_delay": False,
                "financial_hardship": True,
                "rehabilitation_issue": True,
                "protection_issue": True,
            },
        }

        output = self.engine.get_recommendations(payload)
        rec_ids = [r.id for r in output.recommendations]
        
        self.assertIn("REC-ESC-001", rec_ids)
        self.assertIn("REC-PROF-001", rec_ids)
        self.assertIn("REC-TREND-INC", rec_ids)
        self.assertIn("REC-CTX-THREAT", rec_ids)
        self.assertIn("REC-CTX-LEGAL", rec_ids)
        self.assertIn("REC-CTX-FIN", rec_ids)
        self.assertIn("REC-CTX-REHAB", rec_ids)

        # Check strict priority ordering
        priority_map = {"IMMEDIATE": 1, "URGENT": 2, "PRIORITY": 3, "INCREASED": 4, "ROUTINE": 5}
        priorities = [priority_map[r.priority] for r in output.recommendations]
        self.assertEqual(priorities, sorted(priorities), "Recommendations must be sorted by priority rank")

    # -------------------------------------------------------------------------
    # Intent-Based Resource Selection Tests (The 5 QuestionEngine Intents)
    # -------------------------------------------------------------------------

    def test_intent_1_safety_support(self):
        """
        QuestionEngine Intent 1: 'safety_support'
        Expected: Selects safety planning and protection directory resources.
        """
        payload = {
            "case_id": "CASE-INTENT-SAFETY",
            "fused_risk_score": 0.3,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "safety_support",
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-PROT-01", sh_ids, "safety_support intent must include safety planning guide")
        self.assertIn("SH-PROT-02", sh_ids, "safety_support intent must include emergency liaison directory")

    def test_intent_2_event_related_stress(self):
        """
        QuestionEngine Intent 2: 'event_related_stress'
        Expected: Selects post-event stabilization and coping toolkit resources.
        """
        payload = {
            "case_id": "CASE-INTENT-EVENT",
            "fused_risk_score": 0.3,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "event_related_stress",
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-EVENT-01", sh_ids, "event_related_stress intent must include post-event grounding protocol")
        self.assertIn("SH-COP-01", sh_ids, "event_related_stress intent must include coping toolkit")

    def test_intent_3_sleep_functioning(self):
        """
        QuestionEngine Intent 3: 'sleep_functioning'
        Expected: Selects sleep hygiene and somatic relaxation protocols.
        """
        payload = {
            "case_id": "CASE-INTENT-SLEEP",
            "fused_risk_score": 0.2,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "sleep_functioning",
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-WELL-02", sh_ids, "sleep_functioning intent must include sleep hygiene guide")
        self.assertIn("SH-SLEEP-01", sh_ids, "sleep_functioning intent must include somatic sleep protocols")

    def test_intent_4_social_emotional_support(self):
        """
        QuestionEngine Intent 4: 'social_emotional_support'
        Expected: Selects peer support directory and safe communication toolkits.
        """
        payload = {
            "case_id": "CASE-INTENT-SOC",
            "fused_risk_score": 0.2,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "social_emotional_support",
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-SOC-01", sh_ids, "social_emotional_support intent must include peer support network directory")
        self.assertIn("SH-SOC-02", sh_ids, "social_emotional_support intent must include communication toolkit")

    def test_intent_5_general_wellbeing(self):
        """
        QuestionEngine Intent 5: 'general_wellbeing'
        Expected: Selects grounding techniques and holistic resilience guide.
        """
        payload = {
            "case_id": "CASE-INTENT-GW",
            "fused_risk_score": 0.2,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "general_wellbeing",
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-WELL-01", sh_ids, "general_wellbeing intent must include daily grounding techniques")
        self.assertIn("SH-WELL-03", sh_ids, "general_wellbeing intent must include holistic resilience guide")

    def test_multiple_intents_list(self):
        """
        Test providing multiple intents simultaneously in input payload.
        """
        payload = {
            "case_id": "CASE-INTENT-MULTI",
            "fused_risk_score": 0.25,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intents": ["sleep_functioning", "social_emotional_support"],
        }
        output = self.engine.get_recommendations(payload)
        sh_ids = [s.id for s in output.self_help]
        self.assertIn("SH-SLEEP-01", sh_ids)
        self.assertIn("SH-SOC-01", sh_ids)

    def test_invalid_intent_raises_value_error(self):
        """
        Test that unrecognized/invented intent names raise ValueError.
        """
        payload = {
            "case_id": "CASE-INTENT-INVALID",
            "fused_risk_score": 0.2,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "non_existent_invented_intent",
        }
        with self.assertRaises(ValueError):
            self.engine.get_recommendations(payload)

    # -------------------------------------------------------------------------
    # Safety & Determinism Verification Tests
    # -------------------------------------------------------------------------

    def test_safety_phrasing_rules(self):
        """
        Safety Requirement Verification:
        Verify that all generated actions across any scenario are phrased as recommendations/referrals
        and NEVER contain diagnostic, clinical certainty, or treatment mandate phrasing.
        """
        for level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            for trend in ["STABLE", "INCREASING", "DECREASING"]:
                payload = {
                    "case_id": f"TEST-SAFE-{level}-{trend}",
                    "fused_risk_score": 0.5,
                    "risk_level": level,
                    "trend": trend,
                    "context": {
                        "threat_event": True,
                        "investigation_delay": True,
                        "compensation_delay": True,
                        "financial_hardship": True,
                        "rehabilitation_issue": True,
                        "protection_issue": True,
                    },
                }
                res = self.engine.get_recommendations(payload)
                for rec in res.recommendations:
                    for forbidden in FORBIDDEN_DIAGNOSTIC_TERMS:
                        self.assertNotIn(
                            forbidden,
                            rec.action.lower(),
                            f"Forbidden diagnostic term '{forbidden}' in recommendation action: {rec.action}",
                        )
                        self.assertNotIn(
                            forbidden,
                            rec.reason.lower(),
                            f"Forbidden diagnostic term '{forbidden}' in recommendation reason: {rec.reason}",
                        )
                    self.assertTrue(validate_safety_phrasing(rec.action))
                    self.assertTrue(validate_safety_phrasing(rec.reason))

    def test_determinism_consistency(self):
        """
        Determinism Test:
        Run the exact same input 100 times and verify that the output dictionary is byte-for-byte identical.
        """
        payload = {
            "case_id": "CASE-DETERMINISM-01",
            "fused_risk_score": 0.74,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.8,
                "voice_distress": 0.7,
                "behavioural_risk": 0.6,
                "structured_risk": 0.75,
                "temporal_risk": 0.8,
            },
            "context": {
                "threat_event": True,
                "investigation_delay": True,
                "compensation_delay": False,
                "financial_hardship": True,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
            "intent": "safety_support",
        }

        first_run = json.dumps(self.engine.get_recommendations(payload).to_dict(), sort_keys=True)
        for _ in range(100):
            current_run = json.dumps(self.engine.get_recommendations(payload).to_dict(), sort_keys=True)
            self.assertEqual(first_run, current_run, "Recommendation engine output must be completely deterministic")

    def test_convenience_function_dict_interface(self):
        """
        Verify that get_recommendations convenience function works seamlessly with plain dicts.
        """
        data = {
            "case_id": "CASE-CONVENIENCE-01",
            "fused_risk_score": 0.2,
            "risk_level": "LOW",
            "trend": "STABLE",
            "intent": "general_wellbeing",
        }
        res = get_recommendations(data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["case_id"], "CASE-CONVENIENCE-01")
        self.assertEqual(res["risk_level"], "LOW")
        self.assertIsInstance(res["recommendations"], list)
        self.assertIsInstance(res["self_help"], list)


if __name__ == "__main__":
    unittest.main()
