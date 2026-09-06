# MEDHA Recommendation & Intervention Engine

## 1. Overview & Purpose

The **Recommendation + Intervention Module** (`engine/recommendation_engine/`) is a deterministic, explainable, rule-based decision support system for the MEDHA victim assistance platform.

### Core Objectives
- **Zero Internal ML Prediction**: Consumes model signals, fused risk scores, trajectories, contextual flags, and QuestionEngine intents provided by the caller (or future fusion engine).
- **100% Deterministic & Explainable**: Every recommendation is tied directly to transparent trigger conditions and includes an explicit, audit-ready rationale.
- **Strict Non-Diagnostic Safety Guardrails**: All actions are phrased strictly as supportive recommendations, referrals, or assessment protocols—**never** as autonomous medical, clinical, or psychiatric diagnoses.
- **Intent-Aware Self-Help Resource Mapping**: Deterministically selects specialized self-help materials matching MEDHA Question Engine's five defined intents.
- **Completely Decoupled**: Independent from other engines and the in-development fusion layer.

---

## 2. Directory Structure

```
engine/recommendation_engine/
├── __init__.py                # Package exports
├── recommendation_engine.py   # Core RecommendationEngine class & entry points
├── rules.py                   # Rule definitions, context handlers & safety validators
├── schemas.py                 # Dataclass schemas, enums, & dict converters
├── resources.json             # Curated self-help & support resource library
├── test_recommendations.py    # Comprehensive test suite (scenarios 1-7, intent tests, safety, determinism)
└── README.md                  # Documentation and integration guide
```

---

## 3. The Five Defined Question Engine Intents

The recommendation engine natively recognizes and integrates the 5 core intents defined in the MEDHA Question Engine:

| Intent | Domain | Primary Mapped Self-Help Resources |
| :--- | :--- | :--- |
| `safety_support` | Physical & situational safety, threat response | Personal Safety Planning Guide (`SH-PROT-01`), Emergency Liaison Directory (`SH-PROT-02`), 24/7 Crisis Hotline (`SH-CRISIS-01`) |
| `event_related_stress` | Stress triggers following case events or hearings | Post-Event Grounding Protocol (`SH-EVENT-01`), Emotional De-escalation & Coping Toolkit (`SH-COP-01`) |
| `sleep_functioning` | Rest restorative protocols & sleep hygiene | Sleep Hygiene & Routine Restoration Guide (`SH-WELL-02`), Somatic Relaxation Protocols (`SH-SLEEP-01`) |
| `social_emotional_support`| Social isolation, community, and support networks | Peer & Community Support Network Directory (`SH-SOC-01`), Safe Communication & Boundary Setting Toolkit (`SH-SOC-02`) |
| `general_wellbeing` | Routine wellness, baseline monitoring & resilience | Daily Grounding and Breathing Techniques (`SH-WELL-01`), Holistic Daily Wellness Guide (`SH-WELL-03`) |

---

## 4. Input & Output Schemas

### Input Schema

```json
{
  "case_id": "CASE-10492",
  "fused_risk_score": 0.78,
  "risk_level": "HIGH",
  "trend": "INCREASING",
  "intent": "safety_support",
  "signals": {
    "text_distress": 0.82,
    "voice_distress": 0.74,
    "behavioural_risk": 0.70,
    "structured_risk": 0.76,
    "temporal_risk": 0.80
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

### Output Schema

```json
{
  "case_id": "CASE-10492",
  "risk_level": "HIGH",
  "recommendations": [
    {
      "id": "REC-CTX-THREAT",
      "category": "protection",
      "priority": "URGENT",
      "reason": "Active threat event reported in case context.",
      "action": "Assess whether immediate protection support, safety planning, and security measures are required."
    },
    {
      "id": "REC-COUNSEL-002",
      "category": "counselling",
      "priority": "PRIORITY",
      "reason": "Case assessed at HIGH risk level (score: 0.78).",
      "action": "Consider priority counsellor follow-up session within 24 to 48 hours."
    },
    {
      "id": "REC-INTV-001",
      "category": "intervention",
      "priority": "PRIORITY",
      "reason": "Elevated composite risk warrants multi-disciplinary support planning.",
      "action": "Recommend multi-disciplinary case review and tailored support planning."
    },
    {
      "id": "REC-MON-003",
      "category": "monitoring",
      "priority": "PRIORITY",
      "reason": "High risk classification necessitates enhanced monitoring vigilance.",
      "action": "Initiate active high-frequency case monitoring and check-ins."
    },
    {
      "id": "REC-TREND-INC",
      "category": "monitoring",
      "priority": "PRIORITY",
      "reason": "Upward distress trajectory detected across sequential evaluations.",
      "action": "Schedule expedited priority follow-up due to increasing distress trend."
    },
    {
      "id": "REC-CTX-FIN",
      "category": "financial_support",
      "priority": "PRIORITY",
      "reason": "Financial hardship identified in case context.",
      "action": "Provide information on available victim compensation schemes, relief grants, and financial assistance programs."
    }
  ],
  "self_help": [
    {
      "id": "SH-PROT-01",
      "type": "checklist",
      "title": "Personal Safety Planning & Emergency Preparedness Guide",
      "category": "protection",
      "description": "Comprehensive template for establishing safe contacts, secure communication protocols, and situational awareness measures."
    },
    {
      "id": "SH-PROT-02",
      "type": "directory",
      "title": "Emergency Protection & Law Enforcement Liaison Directory",
      "category": "protection",
      "description": "Verified emergency contact numbers, 24/7 dedicated support hotlines, and victim protection liaison resources."
    },
    {
      "id": "SH-FIN-01",
      "type": "directory",
      "title": "Victim Compensation Schemes & Financial Relief Guide",
      "category": "financial_support",
      "description": "Step-by-step guidance on accessing statutory victim compensation funds, emergency subsistence grants, and institutional financial aid services."
    },
    {
      "id": "SH-CRISIS-01",
      "type": "helpline",
      "title": "24/7 National Crisis & Psychological Support Hotline",
      "category": "crisis_support",
      "description": "Immediate access to confidential, round-the-clock trained professional psychological first-aid support services."
    }
  ]
}
```

---

## 5. Rule System Specifications

### Base Risk Rules

| Risk Level | Recommended Actions | Target Priority |
| :--- | :--- | :--- |
| **LOW** | Routine monitoring + supportive wellness resources | `ROUTINE` |
| **MODERATE** | Scheduled counsellor follow-up + increased monitoring cadence + coping toolkit | `INCREASED` |
| **HIGH** | Priority counsellor follow-up (24–48h) + multi-disciplinary support review + active monitoring | `PRIORITY` |
| **CRITICAL** | Immediate escalation to authorized supervisor/response team + urgent professional evaluation | `IMMEDIATE` / `URGENT` |

### Context & Trend Rules

- **Threat Event / Protection Issue**: Triggers protection-support assessment, safety planning checklist, and emergency contact directories (`URGENT` / `PRIORITY`).
- **Financial Hardship / Compensation Delay**: Triggers victim compensation scheme guidance, statutory aid navigation, and liaison assistance (`ROUTINE` / `PRIORITY`).
- **Investigation Delay**: Triggers legal aid advocate and case liaison referral (`ROUTINE`).
- **Rehabilitation Issue**: Triggers community rehabilitation partner directory and social reintegration services (`ROUTINE`).
- **Increasing Distress Trend**: Triggers expedited priority follow-up (`PRIORITY`).

---

## 6. Safety & Ethical Guardrails

1. **Non-Diagnostic Language**: The engine strictly forbids diagnostic conclusions. Recommendations state *"Consider priority counsellor follow-up"* or *"Assess whether protection support is required"*, and never *"Victim requires medical treatment"* or *"Victim is clinically depressed"*.
2. **Automated Safety Filter**: `rules.validate_safety_phrasing()` programmatically inspects generated recommendations before output serialization.

---

## 7. Usage Examples

### Python API

```python
from engine.recommendation_engine import RecommendationEngine, RecommendationEngineInput, Intent

engine = RecommendationEngine()

payload = {
    "case_id": "CASE-101",
    "fused_risk_score": 0.45,
    "risk_level": "MODERATE",
    "trend": "INCREASING",
    "intent": "sleep_functioning",
    "signals": {
        "text_distress": 0.4,
        "voice_distress": 0.5,
        "behavioural_risk": 0.45,
        "structured_risk": 0.35,
        "temporal_risk": 0.6
    },
    "context": {
        "threat_event": False,
        "investigation_delay": False,
        "compensation_delay": False,
        "financial_hardship": False,
        "rehabilitation_issue": False,
        "protection_issue": False
    }
}

output = engine.get_recommendations(payload)
print(output.to_dict())
```

### Functional Convenience Wrapper

```python
from engine.recommendation_engine import get_recommendations

result_dict = get_recommendations(payload)
```

---

## 8. Running Tests

Run the test suite via Python's standard `unittest` or `pytest`:

```bash
# Using python unittest
python -m unittest engine/recommendation_engine/test_recommendations.py

# Or directly
python engine/recommendation_engine/test_recommendations.py
```
