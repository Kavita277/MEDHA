"""
test_recommendation_manual.py
==============================
Manual testing script for MEDHA's Recommendation + Intervention Engine.

Demonstrates 5 realistic cases:
1. LOW + STABLE + general_wellbeing
2. MODERATE + INCREASING + event_related_stress
3. HIGH + INCREASING + safety_support + threat_event
4. HIGH + INCREASING + financial_hardship + social_emotional_support
5. CRITICAL + protection_issue + safety_support
"""

import sys
import os

# Ensure engine package is discoverable
sys.path.insert(0, os.path.abspath("."))

from engine.recommendation_engine import RecommendationEngine


def run_manual_test():
    engine = RecommendationEngine()

    test_cases = [
        {
            "title": "Case 1: LOW + STABLE + general_wellbeing",
            "payload": {
                "case_id": "MEDHA-CASE-001",
                "fused_risk_score": 0.15,
                "risk_level": "LOW",
                "trend": "STABLE",
                "intent": "general_wellbeing",
                "signals": {
                    "text_distress": 0.12,
                    "voice_distress": 0.18,
                    "behavioural_risk": 0.10,
                    "structured_risk": 0.14,
                    "temporal_risk": 0.10,
                },
                "context": {
                    "threat_event": False,
                    "investigation_delay": False,
                    "compensation_delay": False,
                    "financial_hardship": False,
                    "rehabilitation_issue": False,
                    "protection_issue": False,
                },
            },
        },
        {
            "title": "Case 2: MODERATE + INCREASING + event_related_stress",
            "payload": {
                "case_id": "MEDHA-CASE-002",
                "fused_risk_score": 0.48,
                "risk_level": "MODERATE",
                "trend": "INCREASING",
                "intent": "event_related_stress",
                "signals": {
                    "text_distress": 0.45,
                    "voice_distress": 0.52,
                    "behavioural_risk": 0.40,
                    "structured_risk": 0.38,
                    "temporal_risk": 0.60,
                },
                "context": {
                    "threat_event": False,
                    "investigation_delay": False,
                    "compensation_delay": False,
                    "financial_hardship": False,
                    "rehabilitation_issue": False,
                    "protection_issue": False,
                },
            },
        },
        {
            "title": "Case 3: HIGH + INCREASING + safety_support + threat_event",
            "payload": {
                "case_id": "MEDHA-CASE-003",
                "fused_risk_score": 0.78,
                "risk_level": "HIGH",
                "trend": "INCREASING",
                "intent": "safety_support",
                "signals": {
                    "text_distress": 0.80,
                    "voice_distress": 0.75,
                    "behavioural_risk": 0.70,
                    "structured_risk": 0.72,
                    "temporal_risk": 0.82,
                },
                "context": {
                    "threat_event": True,
                    "investigation_delay": False,
                    "compensation_delay": False,
                    "financial_hardship": False,
                    "rehabilitation_issue": False,
                    "protection_issue": False,
                },
            },
        },
        {
            "title": "Case 4: HIGH + INCREASING + financial_hardship + social_emotional_support",
            "payload": {
                "case_id": "MEDHA-CASE-004",
                "fused_risk_score": 0.72,
                "risk_level": "HIGH",
                "trend": "INCREASING",
                "intent": "social_emotional_support",
                "signals": {
                    "text_distress": 0.70,
                    "voice_distress": 0.68,
                    "behavioural_risk": 0.65,
                    "structured_risk": 0.74,
                    "temporal_risk": 0.75,
                },
                "context": {
                    "threat_event": False,
                    "investigation_delay": False,
                    "compensation_delay": False,
                    "financial_hardship": True,
                    "rehabilitation_issue": False,
                    "protection_issue": False,
                },
            },
        },
        {
            "title": "Case 5: CRITICAL + protection_issue + safety_support",
            "payload": {
                "case_id": "MEDHA-CASE-005",
                "fused_risk_score": 0.94,
                "risk_level": "CRITICAL",
                "trend": "INCREASING",
                "intent": "safety_support",
                "signals": {
                    "text_distress": 0.92,
                    "voice_distress": 0.90,
                    "behavioural_risk": 0.95,
                    "structured_risk": 0.88,
                    "temporal_risk": 0.92,
                },
                "context": {
                    "threat_event": False,
                    "investigation_delay": False,
                    "compensation_delay": False,
                    "financial_hardship": False,
                    "rehabilitation_issue": False,
                    "protection_issue": True,
                },
            },
        },
    ]

    for idx, tc in enumerate(test_cases, 1):
        print("=" * 80)
        print(f"[{idx}/5] {tc['title']}")
        print("=" * 80)

        payload = tc["payload"]
        output = engine.get_recommendations(payload)

        # Extract intent from payload for display
        intent_display = payload.get("intent", "None")

        print(f"Case ID    : {output.case_id}")
        print(f"Risk Level : {output.risk_level}")
        print(f"Trend      : {payload.get('trend')}")
        print(f"Intent     : {intent_display}")
        print("-" * 80)
        print("RECOMMENDATIONS:")
        for r_idx, r in enumerate(output.recommendations, 1):
            print(f"  {r_idx}. ID: {r.id}")
            print(f"     Category : {r.category}")
            print(f"     Priority : {r.priority}")
            print(f"     Reason   : {r.reason}")
            print(f"     Action   : {r.action}")
            print()

        print("SELF-HELP RESOURCES:")
        if not output.self_help:
            print("  (None selected)")
        for s_idx, s in enumerate(output.self_help, 1):
            print(f"  {s_idx}. [{s.id}] ({s.type.upper()}) {s.title} [Category: {s.category}]")
            print(f"     Description: {s.description}")
        print("\n")


if __name__ == "__main__":
    run_manual_test()
