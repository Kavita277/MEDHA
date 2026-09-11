# THERAPIST RESULTS GAP AUDIT

## A. CURRENT THERAPIST RESPONSE
Currently, a therapist views case prediction results via the `/api/v1/therapist/cases/{case_id}/results` and `/api/v1/therapist/cases/{case_id}/insights` endpoints.

The `CaseResultResponse` primarily returns numerical predictions and enum flags:
- `results_available` (bool)
- `fusion_dds_prediction` (float)
- `temporal_risk_score` (float)
- `future_escalation_flag` (bool)
- `triage_level` (enum: LOW/MEDIUM/HIGH/CRITICAL)
- `specialists`: Availability flags (`text_available`, `voice_available`) and abstract sub-predictions.

The `CaseInsightsResponse` returns:
- `factors`: A list of `InsightFactor` (category, description, contributing variables) detailing abstract clinical explanations (e.g. "Elevated distress observed in text").

## B. WHAT IS ALREADY USEFUL
The backend excels at exposing the synthesized machine-learning outputs safely to the clinician without exposing raw model internals:
- **Triage Category:** Clearly communicates priority.
- **Fusion DDS / Risk Scores:** Quantifies the current distress level and future escalation risk.
- **Modality Availability:** The `specialists` block transparently indicates exactly which models fired and which were missing (e.g., `behav_blocked: true`).
- **Explainability:** The `factors` array in insights explains *which variables* drove the score.

## C. WHAT IS MISSING
The APIs completely obscure the **human context** of the interaction.
Answering the core questions:
1. **What is happening NOW?** Addressed abstractly (Triage/DDS), but lacks situational awareness.
2. **What changed recently?** Addressed abstractly (Insight factors), but lacks narrative.
3. **What is the current distress level?** Yes (Fusion DDS).
4. **Is future escalation risk available?** Yes.
5. **What is the triage category?** Yes.
6. **What evidence/context produced the result?** Abstract variables only; real context missing.
7. **What did the user say during the conversation?** **MISSING.** Chat history is completely hidden from the therapist APIs.
8. **What check-in information was collected?** **MISSING.** `/checkins` returns timestamps, but the actual questions asked and the patient's answers are omitted.
9. **Which modalities were actually available?** Yes.
10. **What is missing/unavailable?** Yes.
11. **What should the therapist pay attention to next?** Handled by Alerts, but context is lacking.

**The Massive Gap:** The entire `conversation_summary`, `conversation_history`, and `question_history` (which are beautifully collected and stored inside the `SessionModel.state_snapshot`) are completely dropped when serializing the data for the Therapist.

## D. WHAT CAN BE ADDED WITHOUT CHANGING V2
Because the `SessionModel.state_snapshot` dictionary already contains all the missing information, we do not need to alter the V2 architecture, retrain models, or modify the core `ConversationManager` to fix this.

We simply need to update the Pydantic schemas in `backend/schemas/results.py` and `backend/schemas/insights.py` to extract and expose:
1. `conversation_summary` (Current concerns, recent events, unresolved topics).
2. `question_history` (The exact questions the Question Engine selected, and what the user answered).

## E. RECOMMENDED THERAPIST VIEW
To make the dashboard clinically useful, the Therapist endpoint should return a unified view containing:

```json
{
  "clinical_status": {
    "triage_level": "HIGH",
    "fusion_dds_prediction": 0.82,
    "temporal_risk_score": 0.65,
    "future_escalation_flag": true
  },
  "patient_context": {
    "conversation_summary": {
      "current_concerns": ["Overwhelmed by work deadlines"],
      "recent_events": ["Upcoming case-related hearing"],
      "important_observations": ["High text-based distress indicators"]
    },
    "checkin_responses": [
      {
        "question": "Do you currently feel physically safe?",
        "answer": 8.0,
        "intent": "safety_support"
      }
    ]
  },
  "ml_explainability": {
    "factors": [ ... ],
    "modalities_used": ["text", "voice", "structured"]
  }
}
```
This requires no ML changes, just standard API schema mapping from the existing `state_snapshot`.
