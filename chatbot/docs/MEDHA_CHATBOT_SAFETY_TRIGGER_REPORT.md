# MEDHA CHATBOT — SAFETY TRIGGER REPORT

## 1. Objective
Add a dedicated `Safety Trigger` layer that evaluates every user message for explicit, immediate safety concerns and emits an alert to the backend Alert Engine. The trigger must act as an *additive* signal and must not block the conversation from reaching the frozen MEDHA V2 predictive pipeline.

## 2. Existing Safety Architecture Audit
- **Safety Gateway:** The existing `DeterministicSafetyGateway` intercepts responses *after* the NLP extraction if the model detects clinical threats, halting the conversation and returning a crisis message.
- **NLP / Intent:** The existing Text Engine (frozen MuRIL) evaluates continuous signals like `Text_Distress`, `Fear`, and `Urgency`, but does not generate categorical alerts for explicit threats. The chatbot's `GeminiProvider` extracts candidate observations dynamically.
- **Alert Engine:** The repository did not have an existing implemented `AlertEngine`. (A comment referenced one).
- **Conversation Manager:** The main orchestrator where all hooks operate sequentially.

## 3. Final Architecture
The new architecture integrates safely:

```text
User Message
     |
     v
Safety Trigger (NEW)
     |
     +---- [Explicit Threat] ----> Alert Engine (NEW)
     |
     v
Normal Chatbot Flow
(Text Engine -> LLM -> Safety Gateway -> V2 Adapter)
     |
     v
MEDHA V2 Pipeline
```

## 4. Safety Trigger Policy
The `SafetyTrigger` detects only explicit, immediate safety contexts utilizing the LLM Provider but bound by a strict schema. Valid triggers are constrained to:
- `immediate_danger`
- `self_harm_intent`
- `suicidal_intent`
- `threat_to_other`
- `immediate_protection_concern`

## 5. Non-Emergency Policy
Ordinary distress (e.g., "I'm sad", "I'm stressed") does **not** generate an alert. The system specifically distinguishes between general distress (which feeds longitudinal ML prediction) and explicit immediate threats.

## 6. NLP / Intent Strategy
The `SafetyTrigger` reuses the `LLMProviderProtocol` by injecting a specialized classification prompt. It instructs the LLM to identify explicit threats and specifically checks for negations and context (e.g., "I am not suicidal").

## 7. Keyword Limitation
Keyword-only detection was avoided by relying on semantic LLM-based parsing. A phrase like "I read a book about suicide" is understood in context and does not trigger an alert.

## 8. Safety Event Schema
When triggered, a `SafetyEvent` is generated with the following fields:
- `case_id`: The existing victim ID
- `session_id`: The current session ID
- `source`: "chatbot"
- `safety_trigger`: `True`
- `trigger_type`: One of the 5 allowed strings
- `evidence`: Quoted context from the message
- `confidence`: Optional float
- `timestamp`: UTC ISO formatted

## 9. Alert Engine Integration
Since no alert engine existed, an `AlertEngineProtocol` and `MockAlertEngine` were added in `chatbot/safety/safety_trigger.py` to satisfy the requirement and queue urgent alerts without blocking.

## 10. MEDHA Pipeline Continuity
The `ConversationManager` was explicitly designed to wrap the `SafetyTrigger` in a `try...except` and immediately continue to the `TextAdapter` and subsequent hooks. A test (`test_pipeline_continuity_in_conversation_manager`) guarantees that messages that trigger safety events still populate `state.text_features` and continue to the V2 pipeline.

## 11. Existing Safety Gateway Integration
The `SafetyTrigger` runs *first* to alert the backend, but the message still flows to the `SafetyGateway`. If the message also meets the existing criteria for a conversational intercept, the `SafetyGateway` handles the user-facing crisis response just as it did before. The two policies are independent and non-contradictory.

## 12. Frontend Privacy
The UI only interacts with `TurnResult`. The `SafetyEvent` is stored inside `MedhaState.safety_events` for tracing, but is never serialized into the user-facing responses.

## 13. Failure Handling
If the `AlertEngine` throws an error (e.g. network failure), the `SafetyTrigger` catches the exception, logs it, and prevents the chatbot from crashing, allowing the message to still reach MEDHA V2.

## 14. Duplicate/Idempotency Handling
A lightweight check in `SafetyTrigger._is_duplicate()` inspects the last 5 `safety_events` in the state. If the exact same trigger type has been sent recently in the same session, it will deduplicate the alert.

## 15. Test Matrix

| Test Name | Expected Result | Actual Result | Status |
|---|---|---|---|
| 1_explicit_current_danger | Triggers `immediate_danger` | Triggered | PASS |
| 2_explicit_suicidal_intent | Triggers `suicidal_intent` | Triggered | PASS |
| 3_explicit_self_harm_intent | Triggers `self_harm_intent` | Triggered | PASS |
| 4_explicit_imminent_threat_to_another | Triggers `threat_to_other` | Triggered | PASS |
| 5_immediate_protection_concern | Triggers `immediate_protection_concern`| Triggered | PASS |
| 6_normal_sadness | Does NOT trigger | Skipped | PASS |
| 7_normal_stress | Does NOT trigger | Skipped | PASS |
| 8_anger_without_threat | Does NOT trigger | Skipped | PASS |
| 9_negated_suicidal_statement | Does NOT trigger | Skipped | PASS |
| 10_negated_threat_statement | Does NOT trigger | Skipped | PASS |
| 11_historical_safety_event | Does NOT trigger | Skipped | PASS |
| 12_contextual_mention | Does NOT trigger | Skipped | PASS |
| 13_multilingual | Triggers | Triggered | PASS |
| 14_empty_invalid_message | Does NOT trigger | Skipped | PASS |
| 15_llm_unavailable | Graceful fail, no crash | Skipped | PASS |
| 16_alert_engine_unavailable | Graceful fail, no crash | Triggered but no crash| PASS |
| test_idempotency | Duplicate triggers blocked | Blocked | PASS |
| test_pipeline_continuity_in_conversation_manager | Pipeline continues | Features populated | PASS |

## 16. Regression Tests
- **Chatbot Tests (`pytest chatbot/tests -v`):** 146 passed
- **Engine Tests (`pytest engine/tests -v`):** 224 passed
- **Integration Test Status:** PASS

## 17. Files Created
- `chatbot/safety/safety_trigger.py`
- `chatbot/tests/test_safety_trigger.py`
- `chatbot/docs/MEDHA_CHATBOT_SAFETY_TRIGGER_REPORT.md`

## 18. Files Modified
- `chatbot/conversation_manager.py` (Injected safety trigger hook)
- `chatbot/state/medha_state.py` (Added safety events tracking)

## 19. Assumptions
- We assume the LLM provider has sufficient capability to understand context and intent when prompted. 
- We assume the backend alert infrastructure will implement `AlertEngineProtocol` in the future.

## 20. Limitations
- Classification relies on LLM comprehension. Edge cases of extreme nuance might still fail to trigger an alert if the phrasing is sufficiently disguised.

## 21. Frozen Architecture Compliance
- No retraining of models.
- No new DDS/Fusion/GRU engines.
- No modifications to the frozen `engine/` directory.
- No checkpoint modifications.
- Chatbot does not calculate risk scores.
- Chatbot does not diagnose users.
- Normal distress does not trigger alerts.
- Triggered messages continue fully through the MEDHA pipeline.
- Frontend exposes no internal reasoning.

SAFETY TRIGGER STATUS: PASS
