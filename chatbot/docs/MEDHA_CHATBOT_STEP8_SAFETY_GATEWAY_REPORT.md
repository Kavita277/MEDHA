# MEDHA Chatbot — Step 8: Safety Gateway Report

**STEP 8 STATUS: PASS**

## 1. Work Completed
- Implemented `DeterministicSafetyGateway` in `chatbot/safety/safety_gateway.py`.
- Created comprehensive test suite in `chatbot/tests/test_safety_gateway.py`.
- Integrated `DeterministicSafetyGateway` as the default in `ConversationManager`.
- Verified strict separation of conversational safety triggers from predictive ML risk.

## 2. Safety Architecture
**Flow:**
```
User input
→ ConversationManager
→ Safety Gateway (evaluates candidate observations and structured state)
→ returns SafetyResult (triggers escalation if rule matched)
→ Text Engine → LLM Provider...
```
The Safety Gateway intercepts early in the process. Because it relies on `state.candidate_observations` and `state.structured_features`, it can act on observations extracted from previous turns or authoritative structured inputs (like a checkin form), preventing unsafe escalation looping while maintaining a deterministic boundary.

## 3. Authoritative Sources
- **Inspected:** `engine/QuestionEngine/questions.json`, `docs/MEDHA_V2_DATA_CONTRACT.md`, `engine/tests/test_v2_priority_triage.py`, `chatbot/llm/observation_schema.py`.
- **Treated as Authoritative:** `Threat_Event` (0/1), `Recent_Episode` (0/1), and explicitly defined candidate semantic values (`safety` -> `unsafe|in_danger`, `threat_event` -> `present`, `urgency` -> `critical`).

## 4. Safety Policy
- **Conversational Triggers:** Escalates if the LLM extracted a candidate observation for domain `safety` (`unsafe`, `in_danger`), `threat_event` (`present`), or `urgency` (`critical`).
- **Structured Triggers:** Escalates if authoritative `Threat_Event == 1.0` or `Recent_Episode == 1.0`.
- **Exclusions:** Numeric `Safety` score is not used to trigger an emergency due to lack of a defined emergency threshold in the data contract (identified policy gap). ML predictions (`Fusion_DDS_Prediction`, `Temporal_Risk_Score`) are strictly ignored.

## 5. LLM Boundary
The LLM is restricted to extracting qualitative candidate observations based on the strict schema defined in Step 5 (`chatbot/llm/observation_schema.py`). The LLM **cannot** invent a safety policy, escalate on its own, determine thresholds, or declare an emergency based on general negative affect or high stress.

## 6. Evidence and Provenance
`SafetyResult` requires standard metadata containing `source` (e.g., `candidate_observation`, `structured`) and `evidence` (the exact text that triggered the semantic extraction, or the specific structured value).

## 7. Conflict Handling
Authoritative structured features (`Threat_Event=1.0`) trigger the gateway regardless of conversational context (e.g., user saying "I am fine"). The deterministic policy natively handles conflicts by triggering if *any* valid authoritative signal is present.

## 8. Missingness
Missing information (no safety observation, or NaN structured features) results in `is_triggered = False`. It does not invent a "safe" or "unsafe" status. Missing simply means no escalation was triggered.

## 9. Files Created / Modified
**Created:**
- `chatbot/safety/__init__.py`
- `chatbot/safety/safety_gateway.py`
- `chatbot/tests/test_safety_gateway.py`
- `chatbot/docs/MEDHA_CHATBOT_STEP8_SAFETY_GATEWAY_REPORT.md`

**Modified:**
- `chatbot/conversation_manager.py` (Imported and injected new gateway)

**Not Modified:**
- All `engine/` frozen V2 files remained entirely unchanged.

## 10. Tests
- **Safety Gateway Tests:** 7/7 passed (`pytest chatbot/tests/test_safety_gateway.py -v`)
- **Chatbot Test Suite:** 91/91 passed (`pytest chatbot/tests/ -v`)
- **Frozen V2 Engine Suite:** 224/224 passed (`pytest engine/tests/ -v`)
- **Total Failed:** 0

## 11. Architectural Compliance
- No new ML model.
- No new risk model.
- No DDS changes.
- No fusion changes.
- No GRU changes.
- No specialist model changes.
- No feature schema changes.
- No hallucinated numeric mappings.
- No LLM-controlled safety policy.
- No `engine/` modifications.

## 12. Limitations
The numeric scale threshold for emergency on the `Safety` structured feature is undocumented in the repository. As directed, the gateway identifies this as a policy gap and does not invent a threshold.

## 13. Future Work
- Step 9 — Conversation Summary / Important Information
- Step 10 — Behaviour Integration
- Step 11 — Voice Integration
- Step 12 — Chat UI
- Step 13 — Full Integration / Final Testing
