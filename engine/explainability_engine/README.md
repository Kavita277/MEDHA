# MEDHA Explainability Engine

## 1. Overview & Purpose

The **MEDHA Explainability Engine** (`engine/explainability_engine/`) translates upstream risk scores, longitudinal trajectory trends, multi-modal distress signals, and case contextual flags into transparent, deterministic, and support-oriented explanations.

### Core Principles
- **Strict Non-Diagnostic Phrasing**: Explanations never state clinical diagnoses (e.g., "you have depression", "the model diagnosed"). Instead, they employ observational and supportive language (e.g., "was observed in recent interactions", "suggests that additional support may be helpful").
- **100% Deterministic**: Identical inputs produce identical structured explanations every time.
- **Structured Factor Breakdown**: Highlights specific contributing modalities (voice, text, behavioural, structured intake, temporal patterns) and contextual indicators (safety threats, protection concerns, financial hardship, rehabilitation needs).
- **Decoupled Architecture**: Fully independent from internal ML models and the Fusion Engine.

---

## 2. Directory Structure

```
engine/explainability_engine/
├── __init__.py                # Package exports
├── schemas.py                 # Dataclasses, Enums (RiskLevel, Trend, FactorType), converters
├── explainability_engine.py   # Core ExplainabilityEngine logic and safety validation
├── test_explainability.py     # Determinism, safety phrasing, and scenario tests
└── README.md                  # Documentation and API contract
```

---

## 3. Input & Output Contracts

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
  },
  "recent_activity": {
    "checkins": 3,
    "journal_entries": 2,
    "voice_interactions": 1,
    "text_interactions": 2
  }
}
```

### Output Contract

```json
{
  "case_id": "CASE-001",
  "risk_level": "HIGH",
  "summary": "Recent check-ins and increasing distress patterns indicate that prioritized counsellor support is recommended.",
  "factors": [
    {
      "factor": "Recent check-ins",
      "description": "Recent responses indicate increased distress compared with earlier check-ins.",
      "type": "trend"
    },
    {
      "factor": "Voice interaction",
      "description": "Recent voice interaction contributed to the overall assessment.",
      "type": "voice"
    },
    {
      "factor": "Text interaction",
      "description": "Language observed in recent check-ins contributed to the overall assessment.",
      "type": "text"
    },
    {
      "factor": "Temporal pattern",
      "description": "Sequential changes observed over time contributed to the assessment.",
      "type": "temporal"
    },
    {
      "factor": "Interaction patterns",
      "description": "Interaction frequency and response timing patterns were noted during recent check-ins.",
      "type": "behaviour"
    },
    {
      "factor": "Baseline intake profile",
      "description": "Baseline case context and intake profile contributed to the assessment.",
      "type": "structured"
    },
    {
      "factor": "Safety concerns",
      "description": "A safety-related concern was reported in the case context.",
      "type": "context"
    },
    {
      "factor": "Protection needs",
      "description": "A protection-related concern was identified in the case profile.",
      "type": "context"
    },
    {
      "factor": "Financial hardship",
      "description": "Financial strain or hardship was reported in the case context.",
      "type": "context"
    },
    {
      "factor": "Recent engagement",
      "description": "Recorded activity includes 3 check-ins, 2 journal entries, 1 voice interaction, 2 text interactions.",
      "type": "activity"
    }
  ],
  "trend_explanation": "The recent pattern has been increasing.",
  "disclaimer": "This is a support-oriented explanation and is not a medical diagnosis."
}
```

---

## 4. Usage Example

```python
from engine.explainability_engine import ExplainabilityEngine, get_explanation

# Direct dictionary usage
explanation = get_explanation({
    "case_id": "CASE-001",
    "fused_risk_score": 0.76,
    "risk_level": "HIGH",
    "trend": "INCREASING",
    "signals": {"voice_distress": 0.72},
    "context": {"threat_event": True}
})

print(explanation["summary"])
# "Recent check-ins and increasing distress patterns indicate that prioritized counsellor support is recommended."
```
