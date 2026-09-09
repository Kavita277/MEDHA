"""
test_alerts.py
==============
Comprehensive test suite for MEDHA Alert Engine.

Verifies:
1. Scenario 1: LOW + STABLE -> no urgent alert (alert_triggered = False)
2. Scenario 2: MODERATE + STABLE -> attention support notification
3. Scenario 3: MODERATE + INCREASING -> priority support alert
4. Scenario 4: HIGH + STABLE -> priority alert
5. Scenario 5: HIGH + INCREASING -> urgent support alert
6. Scenario 6: HIGH + threat_event -> safety escalation / elevated urgency
7. Scenario 7: CRITICAL -> highest-priority alert (IMMEDIATE)
8. Scenario 8: CRITICAL + protection_issue -> highest-priority safety escalation
9. Deduplication check (is_duplicate_alert)
10. Reason code accumulation across modalities and context
11. Invalid risk level handling
12. Missing required fields handling
13. Determinism (100 runs yield identical output)
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

from alert_engine.schemas import (
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
from alert_engine.alert_engine import (
    AlertEngine,
    get_alert,
    is_duplicate_alert,
)


class TestAlertEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AlertEngine()

    def test_scenario_1_low_stable(self):
        """LOW + STABLE -> no urgent alert triggered"""
        payload = {
            "case_id": "CASE-LOW-1",
            "fused_risk_score": 0.12,
            "risk_level": "LOW",
            "trend": "STABLE",
        }
        res = self.engine.get_alert(payload)
        self.assertFalse(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.ROUTINE.value)
        self.assertEqual(res.alert_type, AlertType.MONITORING.value)
        self.assertIn(ReasonCode.LOW_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.STABLE_TREND.value, res.reason_codes)

    def test_scenario_2_moderate_stable(self):
        """MODERATE + STABLE -> attention/support notification"""
        payload = {
            "case_id": "CASE-MOD-1",
            "fused_risk_score": 0.45,
            "risk_level": "MODERATE",
            "trend": "STABLE",
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.ATTENTION.value)
        self.assertEqual(res.alert_type, AlertType.SUPPORT_NOTIFICATION.value)
        self.assertIn(ReasonCode.MODERATE_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.STABLE_TREND.value, res.reason_codes)

    def test_scenario_3_moderate_increasing(self):
        """MODERATE + INCREASING -> elevated to PRIORITY alert"""
        payload = {
            "case_id": "CASE-MOD-INC",
            "fused_risk_score": 0.55,
            "risk_level": "MODERATE",
            "trend": "INCREASING",
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.PRIORITY.value)
        self.assertEqual(res.alert_type, AlertType.SUPPORT_RISK.value)
        self.assertIn(ReasonCode.MODERATE_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.INCREASING_TREND.value, res.reason_codes)

    def test_scenario_4_high_stable(self):
        """HIGH + STABLE -> priority alert"""
        payload = {
            "case_id": "CASE-HIGH-STABLE",
            "fused_risk_score": 0.72,
            "risk_level": "HIGH",
            "trend": "STABLE",
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.PRIORITY.value)
        self.assertEqual(res.alert_type, AlertType.SUPPORT_RISK.value)
        self.assertIn(ReasonCode.HIGH_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.STABLE_TREND.value, res.reason_codes)

    def test_scenario_5_high_increasing(self):
        """HIGH + INCREASING -> urgent support alert"""
        payload = {
            "case_id": "CASE-HIGH-INC",
            "fused_risk_score": 0.78,
            "risk_level": "HIGH",
            "trend": "INCREASING",
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.URGENT.value)
        self.assertEqual(res.alert_type, AlertType.SUPPORT_RISK.value)
        self.assertIn(ReasonCode.HIGH_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.INCREASING_TREND.value, res.reason_codes)

    def test_scenario_6_high_threat_event(self):
        """HIGH + threat_event -> safety escalation / elevated urgency"""
        payload = {
            "case_id": "CASE-HIGH-THREAT",
            "fused_risk_score": 0.76,
            "risk_level": "HIGH",
            "trend": "STABLE",
            "context": {
                "threat_event": True,
            },
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.URGENT.value)
        self.assertEqual(res.alert_type, AlertType.SAFETY_ESCALATION.value)
        self.assertIn(ReasonCode.THREAT_REPORTED.value, res.reason_codes)

    def test_scenario_7_critical(self):
        """CRITICAL -> highest-priority alert (IMMEDIATE)"""
        payload = {
            "case_id": "CASE-CRIT-1",
            "fused_risk_score": 0.91,
            "risk_level": "CRITICAL",
            "trend": "STABLE",
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.IMMEDIATE.value)
        self.assertEqual(res.alert_type, AlertType.CRISIS_ESCALATION.value)
        self.assertIn(ReasonCode.CRITICAL_RISK.value, res.reason_codes)
        self.assertEqual(res.cta, "Emergency Support Liaison")

    def test_scenario_8_critical_protection_issue(self):
        """CRITICAL + protection_issue -> highest-priority safety escalation"""
        payload = {
            "case_id": "CASE-CRIT-PROT",
            "fused_risk_score": 0.95,
            "risk_level": "CRITICAL",
            "trend": "INCREASING",
            "context": {
                "protection_issue": True,
            },
        }
        res = self.engine.get_alert(payload)
        self.assertTrue(res.alert_triggered)
        self.assertEqual(res.priority, AlertPriority.IMMEDIATE.value)
        self.assertEqual(res.alert_type, AlertType.CRISIS_ESCALATION.value)
        self.assertIn(ReasonCode.CRITICAL_RISK.value, res.reason_codes)
        self.assertIn(ReasonCode.PROTECTION_CONCERN.value, res.reason_codes)
        self.assertIn(ReasonCode.INCREASING_TREND.value, res.reason_codes)

    def test_reason_codes_accumulation_and_modalities(self):
        """Verify comprehensive accumulation of modality and context reason codes"""
        payload = {
            "case_id": "CASE-MULTI-REASON",
            "fused_risk_score": 0.82,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.85,
                "voice_distress": 0.72,
                "behavioural_risk": 0.75,
                "structured_risk": 0.70,
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
        }
        res = self.engine.get_alert(payload)
        expected_codes = [
            ReasonCode.HIGH_RISK.value,
            ReasonCode.INCREASING_TREND.value,
            ReasonCode.THREAT_REPORTED.value,
            ReasonCode.PROTECTION_CONCERN.value,
            ReasonCode.FINANCIAL_HARDSHIP.value,
            ReasonCode.REHABILITATION_ISSUE.value,
            ReasonCode.INVESTIGATION_DELAY.value,
            ReasonCode.COMPENSATION_DELAY.value,
            ReasonCode.HIGH_TEXT_DISTRESS.value,
            ReasonCode.HIGH_VOICE_DISTRESS.value,
            ReasonCode.ELEVATED_BEHAVIOURAL_RISK.value,
            ReasonCode.HIGH_STRUCTURED_RISK.value,
            ReasonCode.HIGH_TEMPORAL_RISK.value,
        ]
        for code in expected_codes:
            self.assertIn(code, res.reason_codes)

    def test_deduplication(self):
        """Verify is_duplicate_alert correctly recognizes identical alert states"""
        payload1 = {
            "case_id": "CASE-DEDUP",
            "fused_risk_score": 0.75,
            "risk_level": "HIGH",
            "trend": "INCREASING",
        }
        alert1 = self.engine.get_alert(payload1)
        alert2 = self.engine.get_alert(payload1)
        self.assertTrue(is_duplicate_alert(alert1, alert2))

        # Different case_id
        payload_diff_case = {
            "case_id": "CASE-DEDUP-2",
            "fused_risk_score": 0.75,
            "risk_level": "HIGH",
            "trend": "INCREASING",
        }
        alert_diff = self.engine.get_alert(payload_diff_case)
        self.assertFalse(is_duplicate_alert(alert1, alert_diff))

        # Changed context
        payload_diff_ctx = {
            "case_id": "CASE-DEDUP",
            "fused_risk_score": 0.75,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "context": {"threat_event": True},
        }
        alert_ctx = self.engine.get_alert(payload_diff_ctx)
        self.assertFalse(is_duplicate_alert(alert1, alert_ctx))

    def test_invalid_risk_level(self):
        """Invalid risk level raises ValueError"""
        with self.assertRaises(ValueError):
            self.engine.get_alert({"case_id": "C-1", "risk_level": "INVALID_RISK"})

    def test_missing_required_fields(self):
        """Missing case_id or risk_level raises ValueError"""
        with self.assertRaises(ValueError):
            self.engine.get_alert({"risk_level": "LOW"})
        with self.assertRaises(ValueError):
            self.engine.get_alert({"case_id": "C-1"})

    def test_determinism_100_runs(self):
        """Identical inputs produce 100% identical alert outputs over 100 runs"""
        payload = {
            "case_id": "CASE-DETERMINISTIC",
            "fused_risk_score": 0.76,
            "risk_level": "HIGH",
            "trend": "INCREASING",
            "signals": {
                "text_distress": 0.80,
                "voice_distress": 0.72,
            },
            "context": {
                "threat_event": True,
            },
        }
        fixed_ts = "2026-09-09T22:00:00Z"
        first = self.engine.get_alert(payload, timestamp=fixed_ts).to_dict()
        for _ in range(100):
            cur = self.engine.get_alert(payload, timestamp=fixed_ts).to_dict()
            self.assertEqual(first, cur)

    def test_required_alert_fields_present(self):
        """Verify alert output contains all required fields: alert_id, case_id, priority, reason, source, recommended_action, timestamp"""
        payload = {
            "case_id": "CASE-REQ-FIELDS",
            "fused_risk_score": 0.75,
            "risk_level": "HIGH",
            "trend": "STABLE",
        }
        alert = self.engine.get_alert(payload)
        out = alert.to_dict()
        required_keys = ["alert_id", "case_id", "priority", "reason", "source", "recommended_action", "timestamp"]
        for key in required_keys:
            self.assertIn(key, out)
            self.assertTrue(bool(out[key]), f"Field '{key}' should not be empty")

    def test_conversational_safety_trigger_keyword(self):
        """Conversational input with explicit physical threat triggers immediate alert"""
        text = "I am afraid for my life, someone is following me outside"
        alert = self.engine.evaluate_conversational_safety(text, case_id="CASE-CONV-1")
        self.assertIsNotNone(alert)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.priority, AlertPriority.URGENT.value)
        self.assertEqual(alert.source, "conversational_safety_trigger")
        self.assertIn(ReasonCode.THREAT_REPORTED.value, alert.reason_codes)
        self.assertIn(ReasonCode.CONVERSATIONAL_SAFETY_CONCERN.value, alert.reason_codes)

    def test_conversational_safety_trigger_nlp_flag(self):
        """Conversational input with safety_concern_mentioned=True triggers immediate alert"""
        alert = self.engine.evaluate_conversational_safety(
            text="I need help with my hearing next week",
            case_id="CASE-CONV-2",
            safety_concern_mentioned=True,
        )
        self.assertIsNotNone(alert)
        self.assertTrue(alert.alert_triggered)
        self.assertEqual(alert.source, "conversational_safety_trigger")

    def test_conversational_safety_safe_text_no_trigger(self):
        """Routine conversational text does not trigger immediate safety alert"""
        text = "I have been feeling a bit tired after work today"
        alert = self.engine.evaluate_conversational_safety(text, case_id="CASE-SAFE")
        self.assertIsNone(alert)


if __name__ == "__main__":
    unittest.main()
