"""
test_pipeline_integration.py
=============================
Integration test suite for MEDHA's Explainability, Alert, and Recommendation Modules.

Tests all 16 specified requirements against Mock Fusion outputs:
1. LOW + STABLE -> no urgent alert
2. MODERATE + STABLE -> attention/support notification
3. MODERATE + INCREASING -> stronger support/follow-up alert (PRIORITY)
4. HIGH + STABLE -> priority alert
5. HIGH + INCREASING -> urgent/priority support alert
6. HIGH + threat_event -> safety-related reason code / elevated urgency
7. CRITICAL -> highest-priority alert (IMMEDIATE)
8. CRITICAL + protection_issue -> highest-priority safety escalation
9. Explainability with all modality signals
10. Explainability with missing optional signals
11. Explainability with only risk level + trend
12. Multiple context factors
13. Invalid risk level handling
14. Invalid/missing required fields
15. Determinism: Run identical input at least 100 times and verify identical output
16. Safety language test: Ensure generated explanations do not contain diagnostic/clinical certainty claims
"""

import unittest
import os
import sys

# Ensure MEDHA and engine directories are in python path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
engine_dir = os.path.join(root_dir, "engine")
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from engine.mock_fusion_data import get_mock_fusion_case
from engine.explainability_engine import (
    ExplainabilityEngine,
    get_explanation,
    validate_safety_phrasing,
    FORBIDDEN_DIAGNOSTIC_TERMS,
)
from engine.alert_engine import (
    AlertEngine,
    get_alert,
    is_duplicate_alert,
    AlertPriority,
    AlertType,
    ReasonCode,
)
from engine.recommendation_engine import (
    RecommendationEngine,
    get_recommendations,
)


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.exp_engine = ExplainabilityEngine()
        self.alert_engine = AlertEngine()
        self.rec_engine = RecommendationEngine()

    # 1. LOW + STABLE -> no urgent alert
    def test_01_low_stable(self):
        mock_data = get_mock_fusion_case("CASE-001-LOW-STABLE")
        
        # Alert Engine
        alert = self.alert_engine.get_alert(mock_data)
        self.assertFalse(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.ROUTINE.value)
        self.assertEqual(alert.alert_type, AlertType.MONITORING.value)

        # Explainability Engine
        exp = self.exp_engine.get_explanation(mock_data)
        self.assertEqual(exp.risk_level, "LOW")
        self.assertIn("stable", exp.summary.lower())

    # 2. MODERATE + STABLE -> attention/support behaviour
    def test_02_moderate_stable(self):
        mock_data = get_mock_fusion_case("CASE-002-MOD-STABLE")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.ATTENTION.value)
        self.assertEqual(alert.alert_type, AlertType.SUPPORT_NOTIFICATION.value)

        exp = self.exp_engine.get_explanation(mock_data)
        self.assertEqual(exp.risk_level, "MODERATE")
        self.assertIn("supportive resources", exp.summary.lower())

    # 3. MODERATE + INCREASING -> stronger support/follow-up alert
    def test_03_moderate_increasing(self):
        mock_data = get_mock_fusion_case("CASE-003-MOD-INC")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.PRIORITY.value)
        self.assertEqual(alert.alert_type, AlertType.SUPPORT_RISK.value)
        self.assertIn(ReasonCode.INCREASING_TREND.value, alert.reason_codes)

        exp = self.exp_engine.get_explanation(mock_data)
        self.assertEqual(exp.trend_explanation, "The recent pattern has been increasing.")

    # 4. HIGH + STABLE -> priority alert
    def test_04_high_stable(self):
        mock_data = get_mock_fusion_case("CASE-004-HIGH-STABLE")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.PRIORITY.value)
        self.assertEqual(alert.alert_type, AlertType.SUPPORT_RISK.value)

        exp = self.exp_engine.get_explanation(mock_data)
        self.assertEqual(exp.risk_level, "HIGH")

    # 5. HIGH + INCREASING -> urgent/priority support alert
    def test_05_high_increasing(self):
        mock_data = get_mock_fusion_case("CASE-005-HIGH-INC")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.URGENT.value)
        self.assertIn(ReasonCode.HIGH_RISK.value, alert.reason_codes)
        self.assertIn(ReasonCode.INCREASING_TREND.value, alert.reason_codes)

        exp = self.exp_engine.get_explanation(mock_data)
        self.assertIn("increasing", exp.summary.lower())

    # 6. HIGH + threat_event -> safety-related reason code / elevated urgency
    def test_06_high_threat_event(self):
        mock_data = get_mock_fusion_case("CASE-006-HIGH-THREAT")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.URGENT.value)
        self.assertEqual(alert.alert_type, AlertType.SAFETY_ESCALATION.value)
        self.assertIn(ReasonCode.THREAT_REPORTED.value, alert.reason_codes)

        exp = self.exp_engine.get_explanation(mock_data)
        context_factors = [f.factor for f in exp.factors if f.type == "context"]
        self.assertIn("Safety concerns", context_factors)

    # 7. CRITICAL -> highest-priority alert
    def test_07_critical(self):
        mock_data = get_mock_fusion_case("CASE-007-CRIT-STABLE")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.IMMEDIATE.value)
        self.assertEqual(alert.alert_type, AlertType.CRISIS_ESCALATION.value)
        self.assertIn(ReasonCode.CRITICAL_RISK.value, alert.reason_codes)

        exp = self.exp_engine.get_explanation(mock_data)
        self.assertIn("immediate support", exp.summary.lower())

    # 8. CRITICAL + protection_issue -> highest-priority safety escalation
    def test_08_critical_protection_issue(self):
        mock_data = get_mock_fusion_case("CASE-008-CRIT-PROT")
        
        alert = self.alert_engine.get_alert(mock_data)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.IMMEDIATE.value)
        self.assertEqual(alert.alert_type, AlertType.CRISIS_ESCALATION.value)
        self.assertIn(ReasonCode.CRITICAL_RISK.value, alert.reason_codes)
        self.assertIn(ReasonCode.PROTECTION_CONCERN.value, alert.reason_codes)

        exp = self.exp_engine.get_explanation(mock_data)
        prot_factor = [f for f in exp.factors if f.factor == "Protection needs"]
        self.assertTrue(len(prot_factor) > 0)

    # 9. Explainability with all modality signals
    def test_09_explainability_all_modality_signals(self):
        mock_data = get_mock_fusion_case("CASE-008-CRIT-PROT")
        exp = self.exp_engine.get_explanation(mock_data)
        
        factor_types = {f.type for f in exp.factors}
        self.assertIn("trend", factor_types)
        self.assertIn("text", factor_types)
        self.assertIn("voice", factor_types)
        self.assertIn("behaviour", factor_types)
        self.assertIn("structured", factor_types)
        self.assertIn("temporal", factor_types)
        self.assertIn("context", factor_types)
        self.assertIn("activity", factor_types)

    # 10. Explainability with missing optional signals
    def test_10_explainability_missing_optional_signals(self):
        minimal_signals = {
            "case_id": "CASE-PARTIAL",
            "fused_risk_score": 0.65,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "signals": {
                "voice_distress": 0.75
                # other modalities omitted
            }
        }
        exp = self.exp_engine.get_explanation(minimal_signals)
        self.assertEqual(exp.case_id, "CASE-PARTIAL")
        voice_factors = [f for f in exp.factors if f.type == "voice"]
        self.assertEqual(len(voice_factors), 1)

    # 11. Explainability with only risk level + trend
    def test_11_explainability_minimal_input(self):
        minimal = {
            "case_id": "CASE-BARE",
            "fused_risk_score": 0.40,
            "risk_level": "MODERATE",
            "trend": "INCREASING",
        }
        exp = self.exp_engine.get_explanation(minimal)
        self.assertEqual(exp.case_id, "CASE-BARE")
        self.assertEqual(exp.trend_explanation, "The recent pattern has been increasing.")
        self.assertTrue(len(exp.summary) > 0)

    # 12. Multiple context factors
    def test_12_multiple_context_factors(self):
        multi_ctx = {
            "case_id": "CASE-MULTI-CTX",
            "fused_risk_score": 0.70,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "context": {
                "threat_event": True,
                "investigation_delay": True,
                "compensation_delay": True,
                "financial_hardship": True,
                "rehabilitation_issue": True,
                "protection_issue": True,
            }
        }
        exp = self.exp_engine.get_explanation(multi_ctx)
        ctx_factors = [f for f in exp.factors if f.type == "context"]
        self.assertEqual(len(ctx_factors), 6)

        alert = self.alert_engine.get_alert(multi_ctx)
        self.assertIn(ReasonCode.THREAT_REPORTED.value, alert.reason_codes)
        self.assertIn(ReasonCode.PROTECTION_CONCERN.value, alert.reason_codes)
        self.assertIn(ReasonCode.FINANCIAL_HARDSHIP.value, alert.reason_codes)
        self.assertIn(ReasonCode.REHABILITATION_ISSUE.value, alert.reason_codes)
        self.assertIn(ReasonCode.INVESTIGATION_DELAY.value, alert.reason_codes)
        self.assertIn(ReasonCode.COMPENSATION_DELAY.value, alert.reason_codes)

    # 13. Invalid risk level
    def test_13_invalid_risk_level(self):
        bad_input = {
            "case_id": "CASE-BAD",
            "fused_risk_score": 0.50,
            "risk_level": "INVALID_LEVEL",
        }
        with self.assertRaises(ValueError):
            self.exp_engine.get_explanation(bad_input)
        with self.assertRaises(ValueError):
            self.alert_engine.get_alert(bad_input)

    # 14. Invalid/missing required fields
    def test_14_invalid_missing_required_fields(self):
        with self.assertRaises(ValueError):
            self.exp_engine.get_explanation({"risk_level": "LOW"})
        with self.assertRaises(ValueError):
            self.alert_engine.get_alert({"fused_risk_score": 0.5})

    # 15. Determinism: 100 runs
    def test_15_determinism_100_runs(self):
        case_data = get_mock_fusion_case("CASE-006-HIGH-THREAT")
        fixed_ts = "2026-09-09T22:00:00Z"
        
        base_exp = self.exp_engine.get_explanation(case_data).to_dict()
        base_alert = self.alert_engine.get_alert(case_data, timestamp=fixed_ts).to_dict()
        base_rec = self.rec_engine.get_recommendations(case_data).to_dict()

        for _ in range(100):
            cur_exp = self.exp_engine.get_explanation(case_data).to_dict()
            cur_alert = self.alert_engine.get_alert(case_data, timestamp=fixed_ts).to_dict()
            cur_rec = self.rec_engine.get_recommendations(case_data).to_dict()

            self.assertEqual(base_exp, cur_exp)
            self.assertEqual(base_alert, cur_alert)
            self.assertEqual(base_rec, cur_rec)

    # 16. Safety language test: Ensure explanations never make clinical/diagnostic claims
    def test_16_safety_language(self):
        for case_key in ["CASE-001-LOW-STABLE", "CASE-003-MOD-INC", "CASE-006-HIGH-THREAT", "CASE-008-CRIT-PROT"]:
            case_data = get_mock_fusion_case(case_key)
            exp = self.exp_engine.get_explanation(case_data)
            exp_dict = exp.to_dict()

            self.assertTrue(validate_safety_phrasing(exp.summary))
            self.assertTrue(validate_safety_phrasing(exp.trend_explanation))
            for f in exp.factors:
                self.assertTrue(validate_safety_phrasing(f.factor))
                self.assertTrue(validate_safety_phrasing(f.description))

            full_text = str(exp_dict).lower()
            for forbidden in FORBIDDEN_DIAGNOSTIC_TERMS:
                self.assertNotIn(forbidden, full_text)

    # 17. End-to-End Pipeline: User interaction -> Modality Signals -> Fusion -> Downstream Engines
    def test_17_full_end_to_end_pipeline(self):
        """
        Demonstrates the complete multi-modal pipeline:
        User interaction -> Modality extraction -> Fusion -> Explainability, Alert, Recommendation
        """
        # Step 1: User interaction signals
        user_interaction = {
            "case_id": "CASE-E2E-100",
            "text_response": "I have been feeling increasingly stressed and having trouble sleeping.",
            "voice_recording_available": True,
        }

        # Step 2: Modality feature extractors
        text_signals = {"text_distress": 0.78, "fear_signal": 0.65}
        voice_signals = {"voice_distress": 0.72, "voice_confidence": 0.50}
        behaviour_signals = {"behavioural_risk": 0.68}
        structured_signals = {"structured_risk": 0.74}
        temporal_signals = {"temporal_risk": 0.76}

        # Step 3: Fusion module contract output
        fusion_output = {
            "case_id": user_interaction["case_id"],
            "fused_risk_score": 0.77,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": text_signals["text_distress"],
                "voice_distress": voice_signals["voice_distress"],
                "behavioural_risk": behaviour_signals["behavioural_risk"],
                "structured_risk": structured_signals["structured_risk"],
                "temporal_risk": temporal_signals["temporal_risk"],
            },
            "context": {
                "threat_event": False,
                "investigation_delay": False,
                "compensation_delay": False,
                "financial_hardship": True,
                "rehabilitation_issue": False,
                "protection_issue": False,
            },
            "recent_activity": {
                "checkins": 3,
                "journal_entries": 2,
                "voice_interactions": 1,
                "text_interactions": 2,
            },
        }

        # Step 4: Downstream Explainability Engine
        exp_res = self.exp_engine.get_explanation(fusion_output)
        self.assertEqual(exp_res.case_id, "CASE-E2E-100")
        self.assertEqual(exp_res.risk_level, "HIGH")
        self.assertIn("increasing", exp_res.summary.lower())
        self.assertEqual(exp_res.trend_explanation, "The recent pattern has been increasing.")

        # Step 5: Downstream Alert Engine
        alert_res = self.alert_engine.get_alert(fusion_output)
        self.assertTrue(alert_res.alert_triggered)
        self.assertEqual(alert_res.priority, AlertPriority.URGENT.value)
        self.assertEqual(alert_res.alert_type, AlertType.SUPPORT_RISK.value)
        self.assertIn(ReasonCode.HIGH_RISK.value, alert_res.reason_codes)
        self.assertIn(ReasonCode.INCREASING_TREND.value, alert_res.reason_codes)
        self.assertIn(ReasonCode.FINANCIAL_HARDSHIP.value, alert_res.reason_codes)
        self.assertEqual(alert_res.cta, "Talk to a Counsellor")

        # Step 6: Downstream Recommendation Engine
        rec_res = self.rec_engine.get_recommendations(fusion_output)
        self.assertEqual(rec_res.case_id, "CASE-E2E-100")
        self.assertTrue(len(rec_res.recommendations) > 0)
        self.assertTrue(len(rec_res.self_help) > 0)

    # 18. Immediate Conversational Safety Trigger
    def test_18_immediate_conversational_safety_trigger(self):
        """
        Demonstrates the separate immediate fast-path safety trigger:
        Explicit physical safety statement in conversational input immediately triggers an urgent alert
        without waiting for the asynchronous multi-modal fusion cycle.
        """
        conversational_input = "He threatened to kill me if I attend the hearing next week."
        case_id = "CASE-SAFETY-URGENT"

        # Fast-path safety evaluation
        immediate_alert = self.alert_engine.evaluate_conversational_safety(
            text=conversational_input,
            case_id=case_id,
        )

        self.assertIsNotNone(immediate_alert)
        self.assertTrue(immediate_alert.alert_triggered)
        self.assertEqual(immediate_alert.priority, AlertPriority.URGENT.value)
        self.assertEqual(immediate_alert.source, "conversational_safety_trigger")
        self.assertEqual(immediate_alert.alert_type, AlertType.SAFETY_ESCALATION.value)
        self.assertIn(ReasonCode.THREAT_REPORTED.value, immediate_alert.reason_codes)
        self.assertIn(ReasonCode.CONVERSATIONAL_SAFETY_CONCERN.value, immediate_alert.reason_codes)
        self.assertEqual(immediate_alert.cta, "Review Safety Support")


if __name__ == "__main__":
    unittest.main()
