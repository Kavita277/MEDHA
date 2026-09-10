# MEDHA Chatbot — Step 7: Question Engine Report

**Status:** IMPLEMENTED AND TESTED
**Total Engine Tests Passed:** 224/224
**Total Chatbot Tests Passed:** 84/84

## Architectural Compliance

Step 7 implemented the deterministic Question Engine, explicitly isolating clinical questioning strategy from LLM hallucination.

### Implemented Policies

1. **Deterministic Sourcing:**
   - The engine loads its question bank strictly from the frozen V2 `engine/QuestionEngine/questions.json`.
   - It respects the exact wording, intents, priority levels, and metadata baked into the V2 registry.

2. **Missingness Targeting (Context-Aware):**
   - The policy checks `MedhaState.structured_features` and `MedhaState.candidate_observations`.
   - If a core feature (like `Sleep` or `Safety`) is completely missing (not in structured data AND not recently extracted as a candidate observation), the engine triggers the corresponding question ID (e.g. `SF-01` or `SA-01`).
   - If a candidate observation exists (e.g., the LLM noted `sleep: poor` from conversation), the engine suppresses the question, ensuring the conversation feels natural and does not interrogate the user for information they just volunteered.

3. **Strict Priority Selection:**
   - If multiple core areas are missing, the engine sorts candidates by V2-defined priority:
     - Priority 1: `Safety` -> `SA-01`
     - Priority 2: `Stress` -> `ES-01` / `ES-02`
     - Priority 3: `Sleep` -> `SF-01`, `Functioning` -> `SF-02`, `Social Support` -> `SE-01`
     - Priority 4: `Mood` (Wellbeing) -> `GW-01`
   - It returns a maximum of **one** question per evaluation, preventing overwhelming the user.

4. **Cooldown Enforcement:**
   - The engine honors `cooldown_days` from `questions.json`. If a question was recently asked (recorded in `MedhaState.question_history`), it is filtered out to prevent repetitive looping.

## Integration & Verification

- `DeterministicQuestionEngine` was securely injected into `ConversationManager.process_message`.
- The engine's selected `QuestionRecord` is attached to `MedhaState` and passed to the `LLMProvider` so the LLM can phrase the strict clinical question naturally without altering its semantic intent.
- 5 new tests in `test_question_engine.py` verify priority, frequency, missingness suppression, and cooldowns.
- All 84 chatbot tests passed. All 224 engine tests passed.
