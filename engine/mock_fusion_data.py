"""
mock_fusion_data.py
===================
MOCK FUSION INPUT - FOR TESTING AND INTEGRATION ONLY.

================================================================================
NOTICE:
This file contains mock fixtures simulating output from the in-development Fusion Module.
It does NOT perform ML fusion or prediction. When the real Fusion module is merged,
these mock structures should be directly replaceable by the true Fusion engine output.
================================================================================
"""

from typing import Dict, Any, List

MOCK_FUSION_CASES: Dict[str, Dict[str, Any]] = {
    # 1. LOW + STABLE
    "CASE-001-LOW-STABLE": {
        "case_id": "CASE-001-LOW-STABLE",
        "fused_risk_score": 0.15,
        "risk_level": "LOW",
        "trend": "STABLE",
        "signals": {
            "text_distress": 0.12,
            "voice_distress": 0.15,
            "behavioural_risk": 0.10,
            "structured_risk": 0.20,
            "temporal_risk": 0.14,
        },
        "context": {
            "threat_event": False,
            "investigation_delay": False,
            "compensation_delay": False,
            "financial_hardship": False,
            "rehabilitation_issue": False,
            "protection_issue": False,
        },
        "recent_activity": {
            "checkins": 4,
            "journal_entries": 3,
            "voice_interactions": 2,
            "text_interactions": 2,
        },
    },

    # 2. MODERATE + STABLE
    "CASE-002-MOD-STABLE": {
        "case_id": "CASE-002-MOD-STABLE",
        "fused_risk_score": 0.48,
        "risk_level": "MODERATE",
        "trend": "STABLE",
        "signals": {
            "text_distress": 0.50,
            "voice_distress": 0.45,
            "behavioural_risk": 0.42,
            "structured_risk": 0.40,
            "temporal_risk": 0.46,
        },
        "context": {
            "threat_event": False,
            "investigation_delay": True,
            "compensation_delay": False,
            "financial_hardship": False,
            "rehabilitation_issue": False,
            "protection_issue": False,
        },
        "recent_activity": {
            "checkins": 2,
            "journal_entries": 1,
            "voice_interactions": 1,
            "text_interactions": 1,
        },
    },

    # 3. MODERATE + INCREASING
    "CASE-003-MOD-INC": {
        "case_id": "CASE-003-MOD-INC",
        "fused_risk_score": 0.58,
        "risk_level": "MODERATE",
        "trend": "INCREASING",
        "signals": {
            "text_distress": 0.65,
            "voice_distress": 0.62,
            "behavioural_risk": 0.54,
            "structured_risk": 0.45,
            "temporal_risk": 0.68,
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
    },

    # 4. HIGH + STABLE
    "CASE-004-HIGH-STABLE": {
        "case_id": "CASE-004-HIGH-STABLE",
        "fused_risk_score": 0.72,
        "risk_level": "HIGH",
        "trend": "STABLE",
        "signals": {
            "text_distress": 0.74,
            "voice_distress": 0.70,
            "behavioural_risk": 0.65,
            "structured_risk": 0.68,
            "temporal_risk": 0.71,
        },
        "context": {
            "threat_event": False,
            "investigation_delay": False,
            "compensation_delay": True,
            "financial_hardship": True,
            "rehabilitation_issue": False,
            "protection_issue": False,
        },
        "recent_activity": {
            "checkins": 2,
            "journal_entries": 1,
            "voice_interactions": 2,
            "text_interactions": 1,
        },
    },

    # 5. HIGH + INCREASING
    "CASE-005-HIGH-INC": {
        "case_id": "CASE-005-HIGH-INC",
        "fused_risk_score": 0.78,
        "risk_level": "HIGH",
        "trend": "INCREASING",
        "signals": {
            "text_distress": 0.82,
            "voice_distress": 0.76,
            "behavioural_risk": 0.70,
            "structured_risk": 0.72,
            "temporal_risk": 0.80,
        },
        "context": {
            "threat_event": False,
            "investigation_delay": True,
            "compensation_delay": False,
            "financial_hardship": True,
            "rehabilitation_issue": True,
            "protection_issue": False,
        },
        "recent_activity": {
            "checkins": 4,
            "journal_entries": 3,
            "voice_interactions": 2,
            "text_interactions": 3,
        },
    },

    # 6. HIGH + THREAT EVENT
    "CASE-006-HIGH-THREAT": {
        "case_id": "CASE-006-HIGH-THREAT",
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
            "investigation_delay": False,
            "compensation_delay": False,
            "financial_hardship": True,
            "rehabilitation_issue": False,
            "protection_issue": True,
        },
        "recent_activity": {
            "checkins": 3,
            "journal_entries": 2,
            "voice_interactions": 1,
            "text_interactions": 2,
        },
    },

    # 7. CRITICAL + STABLE
    "CASE-007-CRIT-STABLE": {
        "case_id": "CASE-007-CRIT-STABLE",
        "fused_risk_score": 0.92,
        "risk_level": "CRITICAL",
        "trend": "STABLE",
        "signals": {
            "text_distress": 0.90,
            "voice_distress": 0.88,
            "behavioural_risk": 0.85,
            "structured_risk": 0.86,
            "temporal_risk": 0.89,
        },
        "context": {
            "threat_event": False,
            "investigation_delay": True,
            "compensation_delay": True,
            "financial_hardship": True,
            "rehabilitation_issue": True,
            "protection_issue": False,
        },
        "recent_activity": {
            "checkins": 1,
            "journal_entries": 0,
            "voice_interactions": 1,
            "text_interactions": 1,
        },
    },

    # 8. CRITICAL + PROTECTION ISSUE
    "CASE-008-CRIT-PROT": {
        "case_id": "CASE-008-CRIT-PROT",
        "fused_risk_score": 0.96,
        "risk_level": "CRITICAL",
        "trend": "INCREASING",
        "signals": {
            "text_distress": 0.95,
            "voice_distress": 0.92,
            "behavioural_risk": 0.88,
            "structured_risk": 0.90,
            "temporal_risk": 0.94,
        },
        "context": {
            "threat_event": True,
            "investigation_delay": False,
            "compensation_delay": False,
            "financial_hardship": True,
            "rehabilitation_issue": False,
            "protection_issue": True,
        },
        "recent_activity": {
            "checkins": 5,
            "journal_entries": 4,
            "voice_interactions": 3,
            "text_interactions": 4,
        },
    },
}


def get_mock_fusion_case(case_name: str) -> Dict[str, Any]:
    """
    Retrieve a mock fusion payload by name.
    """
    if case_name not in MOCK_FUSION_CASES:
        raise KeyError(f"Mock case '{case_name}' not found. Available: {list(MOCK_FUSION_CASES.keys())}")
    return dict(MOCK_FUSION_CASES[case_name])


def list_mock_fusion_cases() -> List[str]:
    """
    List all available mock fusion case names.
    """
    return list(MOCK_FUSION_CASES.keys())
