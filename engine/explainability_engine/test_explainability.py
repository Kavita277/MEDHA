"""
test_explainability.py
======================
Comprehensive test suite for MEDHA Explainability Engine.

Verifies:
1. LOW risk explanation
2. MODERATE + INCREASING explanation
3. HIGH + Threat Event explanation
4. CRITICAL + Protection Issue explanation
5. All modality signals present
6. Missing optional signals
7. Minimal input (only risk_level + trend)
8. Multiple context factors
9. Invalid risk level handling
10. Invalid / missing required fields
11. Determinism (100 runs yield identical output)
12. Safety language verification (no diagnostic certainty claims)
"""

import unittest
import os
import sys

# Ensure package root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from explainability_engine.schemas import (
    ExplainabilityInput,
    ExplainabilityOutput,
    RiskLevel,
    Trend,
    FactorType,
    SignalsInput,
    ContextInput,
    RecentActivityInput,
)
from explainability_engine.explainability_engine import (
    ExplainabilityEngine,
    get_explanation,
    FORBIDDEN_DIAGNOSTIC_TERMS,
    validate_safety_phrasing,
)


class TestExplainabilityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ExplainabilityEngine()

    def test_low_stable_explanation(self):
        """LOW risk + STABLE trend -> routine/stable summary"""
        payload = {
            "case_id": "CASE-LOW",
            "fused_risk_score": 0.15,
            "risk_level": "LOW",
            "trend": "STABLE",
            "signals": {
                "text_distress": 0.10,
                "voice_distress": 0.12,
            },
        }
        res = self.engine.get_explanation(payload)
        self.assertEqual(res.case_id, "CASE-LOW")
        self.assertEqual(res.risk_level, "LOW")
        self.assertIn("stable", res.summary.lower())
        self.assertEqual(res.trend_explanation, "The recent pattern has been stable.")
        self.assertIn("not a medical diagnosis", res.disclaimer)

    def test_moderate_increasing_explanation(self):
        """MODERATE + INCREASING trend -> explains increasing pattern"""
        payload = {
            "case_id": "CASE-MOD",
            "fused_risk_score": 0.52,
            "risk_level": "MODERATE",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.65,
            },
        }
        res = self.engine.get_explanation(payload)
        self.assertIn("increasing", res.summary.lower())
        self.assertEqual(res.trend_explanation, "The recent pattern has been increasing.")
        
        # Check trend factor exists
        trend_factors = [f for f in res.factors if f.type == FactorType.TREND.value]
        self.assertTrue(len(trend_factors) > 0)
        self.assertIn("increased distress", trend_factors[0].description)

        # Check text factor exists
        text_factors = [f for f in res.factors if f.type == FactorType.TEXT.value]
        self.assertTrue(len(text_factors) > 0)

    def test_high_threat_explanation(self):
        """HIGH risk + Threat event -> safety context factor"""
        payload = {
            "case_id": "CASE-HIGH",
            "fused_risk_score": 0.76,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "voice_distress": 0.72,
                "structured_risk": 0.74,
            },
            "context": {
                "threat_event": True,
                "financial_hardship": True,
            },
        }
        res = self.engine.get_explanation(payload)
        self.assertEqual(res.risk_level, "HIGH")

        context_factors = [f for f in res.factors if f.type == FactorType.CONTEXT.value]
        factor_names = [f.factor for f in context_factors]
        self.assertIn("Safety concerns", factor_names)
        self.assertIn("Financial hardship", factor_names)

    def test_critical_protection_explanation(self):
        """CRITICAL + Protection issue -> immediate support summary & protection factor"""
        payload = {
            "case_id": "CASE-CRIT",
            "fused_risk_score": 0.92,
            "risk_level": "CRITICAL",
            "trend": "INCREASING",
            "context": {
                "protection_issue": True,
            },
        }
        res = self.engine.get_explanation(payload)
        self.assertIn("immediate support", res.summary.lower())
        
        prot_factors = [f for f in res.factors if f.factor == "Protection needs"]
        self.assertTrue(len(prot_factors) > 0)

    def test_all_modality_signals_present(self):
        """All modality signals present and above threshold"""
        payload = {
            "case_id": "CASE-ALL-SIG",
            "fused_risk_score": 0.85,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.80,
                "voice_distress": 0.75,
                "behavioural_risk": 0.70,
                "structured_risk": 0.72,
                "temporal_risk": 0.78,
            },
            "context": {
                "threat_event": True,
                "protection_issue": True,
                "financial_hardship": True,
                "rehabilitation_issue": True,
                "investigation_delay": True,
                "compensation_delay": True,
            },
            "recent_activity": {
                "checkins": 3,
                "journal_entries": 2,
                "voice_interactions": 1,
                "text_interactions": 2,
            },
        }
        res = self.engine.get_explanation(payload)
        factor_types = {f.type for f in res.factors}
        self.assertIn(FactorType.TREND.value, factor_types)
        self.assertIn(FactorType.TEXT.value, factor_types)
        self.assertIn(FactorType.VOICE.value, factor_types)
        self.assertIn(FactorType.BEHAVIOUR.value, factor_types)
        self.assertIn(FactorType.STRUCTURED.value, factor_types)
        self.assertIn(FactorType.TEMPORAL.value, factor_types)
        self.assertIn(FactorType.CONTEXT.value, factor_types)
        self.assertIn(FactorType.ACTIVITY.value, factor_types)

    def test_missing_optional_signals(self):
        """Signals and context omitted should not crash engine"""
        payload = {
            "case_id": "CASE-MINIMAL",
            "fused_risk_score": 0.45,
            "risk_level": "MODERATE",
            "trend": "STABLE",
        }
        res = self.engine.get_explanation(payload)
        self.assertEqual(res.case_id, "CASE-MINIMAL")
        self.assertEqual(res.risk_level, "MODERATE")
        self.assertTrue(len(res.summary) > 0)

    def test_invalid_risk_level(self):
        """Invalid risk level raises ValueError"""
        payload = {
            "case_id": "CASE-INV",
            "fused_risk_score": 0.5,
            "risk_level": "SUPER_HIGH",
        }
        with self.assertRaises(ValueError):
            self.engine.get_explanation(payload)

    def test_missing_required_fields(self):
        """Missing case_id or fused_risk_score raises ValueError"""
        with self.assertRaises(ValueError):
            self.engine.get_explanation({"fused_risk_score": 0.5, "risk_level": "LOW"})
        with self.assertRaises(ValueError):
            self.engine.get_explanation({"case_id": "C-1", "risk_level": "LOW"})

    def test_determinism_100_runs(self):
        """Identical inputs produce 100% identical outputs over 100 runs"""
        payload = {
            "case_id": "CASE-DETERMINISTIC",
            "fused_risk_score": 0.76,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.80,
                "voice_distress": 0.72,
                "behavioural_risk": 0.68,
                "structured_risk": 0.74,
                "temporal_risk": 0.78,
            },
            "context": {
                "threat_event": True,
                "protection_issue": True,
                "financial_hardship": True,
            },
            "recent_activity": {
                "checkins": 3,
                "journal_entries": 2,
            },
        }
        first_output = self.engine.get_explanation(payload).to_dict()
        for _ in range(100):
            current_output = self.engine.get_explanation(payload).to_dict()
            self.assertEqual(first_output, current_output)

    def test_safety_language(self):
        """Output never contains forbidden diagnostic or clinical assertion phrasing"""
        scenarios = [
            {"case_id": "C1", "fused_risk_score": 0.1, "risk_level": "LOW", "trend": "STABLE"},
            {"case_id": "C2", "fused_risk_score": 0.5, "risk_level": "MODERATE", "trend": "INCREASING"},
            {"case_id": "C3", "fused_risk_score": 0.75, "risk_level": "HIGH", "trend": "INCREASING", "context": {"threat_event": True}},
            {"case_id": "C4", "fused_risk_score": 0.95, "risk_level": "CRITICAL", "trend": "INCREASING", "context": {"protection_issue": True}},
        ]
        for sc in scenarios:
            res = self.engine.get_explanation(sc)
            out_dict = res.to_dict()
            self.assertTrue(validate_safety_phrasing(res.summary))
            self.assertTrue(validate_safety_phrasing(res.trend_explanation))
            for f in res.factors:
                self.assertTrue(validate_safety_phrasing(f.description))
                self.assertTrue(validate_safety_phrasing(f.factor))
            
            # String search in all text fields
            full_text = str(out_dict).lower()
            for forbidden in FORBIDDEN_DIAGNOSTIC_TERMS:
                self.assertNotIn(forbidden, full_text)


if __name__ == "__main__":
    unittest.main()
