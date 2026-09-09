# MEDHA Alert Engine

## 1. Overview & Purpose

The **MEDHA Alert Engine** (`engine/alert_engine/`) evaluates upstream risk scores, trajectory trends, multi-modal distress signals, and contextual events to produce deterministic, safe, support-oriented alerts with prioritized Call-to-Actions (CTAs).

### Core Principles
- **Downstream Only**: Does NOT compute or override ML risk scores. It solely decides notification urgency and actions based on upstream outputs.
- **Deterministic Priority Policy**: Transparent, rules-based mapping from risk levels and context flags to alert priorities.
- **Configurable & Safe**: Uses non-diagnostic, supportive language, and provides configurable templates for emergency/support routing.
- **Deduplication Ready**: Generates stable alert IDs and fingerprinting utilities to prevent repetitive notification spam across longitudinal check-ins.

---

## 2. Directory Structure

```
engine/alert_engine/
├── __init__.py           # Package exports
├── schemas.py            # Dataclass schemas, Enums (AlertPriority, AlertType, ReasonCode)
├── alert_engine.py       # Core evaluation rules, priority matrix, deduplication logic
├── test_alerts.py        # Comprehensive test suite (scenarios 1-8, deduplication, determinism)
└── README.md             # Documentation and integration guide
```

---

## 3. Priority & Routing Policy

| Upstream Risk | Trajectory / Context | Alert Triggered | Priority | Alert Type | Recommended Action / CTA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LOW** | STABLE / DECREASING | `False` | `ROUTINE` | `MONITORING` | Maintain regular check-in schedule (`View Wellness Resources`) |
| **LOW** | Threat / Protection Flag | `True` | `URGENT` | `SAFETY_ESCALATION` | Review safety precautions (`Review Safety Support`) |
| **MODERATE**| STABLE / DECREASING | `True` | `ATTENTION` | `SUPPORT_NOTIFICATION` | Explore available support resources (`Explore Support Options`) |
| **MODERATE**| INCREASING | `True` | `PRIORITY` | `SUPPORT_RISK` | Connect with a counsellor or support team (`Connect with Support`) |
| **MODERATE**| Threat / Protection Flag | `True` | `URGENT` | `SAFETY_ESCALATION` | Review safety support protocols (`Connect with Support`) |
| **HIGH** | STABLE / DECREASING | `True` | `PRIORITY` | `SUPPORT_RISK` | Connect with a counsellor for follow-up (`Talk to a Counsellor`) |
| **HIGH** | INCREASING | `True` | `URGENT` | `SUPPORT_RISK` | Priority counsellor follow-up (`Talk to a Counsellor`) |
| **HIGH** | Threat / Protection Flag | `True` | `URGENT` | `SAFETY_ESCALATION` | Connect with counsellor & review protection protocols (`Talk to a Counsellor`) |
| **CRITICAL**| Any | `True` | `IMMEDIATE` | `CRISIS_ESCALATION` | Immediate crisis escalation (`Emergency Support Liaison`) |

---

## 4. Input & Output Contracts

### Input Contract

```json
{
  "case_id": "CASE-001",
  "fused_risk_score": 0.76,
  "risk_level": "HIGH",
  "trend": "INCREASING",
  "signals": {
    "text_distress": 0.80,
    "voice_distress": 0.72,
    "behavioural_risk": 0.68,
    "structured_risk": 0.74,
    "temporal_risk": 0.78
  },
  "context": {
    "threat_event": true,
    "investigation_delay": false,
    "compensation_delay": false,
    "financial_hardship": true,
    "rehabilitation_issue": false,
    "protection_issue": true
  }
}
```

### Output Contract

```json
{
  "alert_id": "ALT-CASE-001-c7a8b9e1",
  "case_id": "CASE-001",
  "alert_triggered": true,
  "priority": "URGENT",
  "alert_type": "SAFETY_ESCALATION",
  "title": "High Priority Safety Alert",
  "message": "High risk assessment accompanied by safety concerns indicates prioritized support is required.",
  "recommended_action": "Connect with a counsellor and review case protection protocols.",
  "cta": "Talk to a Counsellor",
  "reason_codes": [
    "HIGH_RISK",
    "INCREASING_TREND",
    "THREAT_REPORTED",
    "PROTECTION_CONCERN",
    "FINANCIAL_HARDSHIP",
    "HIGH_TEXT_DISTRESS",
    "HIGH_VOICE_DISTRESS",
    "HIGH_STRUCTURED_RISK",
    "HIGH_TEMPORAL_RISK"
  ],
  "status": "NEW"
}
```

---

## 5. Usage & Deduplication Example

```python
from engine.alert_engine import AlertEngine, get_alert, is_duplicate_alert

engine = AlertEngine()

alert1 = engine.get_alert({
    "case_id": "CASE-001",
    "fused_risk_score": 0.76,
    "risk_level": "HIGH",
    "trend": "INCREASING"
})

alert2 = engine.get_alert({
    "case_id": "CASE-001",
    "fused_risk_score": 0.76,
    "risk_level": "HIGH",
    "trend": "INCREASING"
})

print(is_duplicate_alert(alert1, alert2))
# True -> Prevents duplicate notification spam
```
