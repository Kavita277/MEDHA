# MEDHA Chatbot — Step 6: Feature Mapper & Validator Report

**Status:** IMPLEMENTED AND TESTED
**Total Engine Tests Passed:** 224/224
**Total Chatbot Tests Passed:** 79/79

## Architectural Compliance

Step 6 required the creation of a deterministic boundary between the LLM's conversational semantic observations and MEDHA V2's strict numeric predictive features. The implementation strictly adheres to the Absolute Architecture Rule: **The existing V2 system is authoritative, and its feature schemas cannot be altered.**

### Implemented Policies

1. **Strict Type and Mapping Rejection:**
   - The MEDHA V2 GRU model and Specialist Predictors expect features like `Sleep`, `Mood`, and `Stress` to be bounded integers (1-5) derived from rigid Question Engine survey scales (e.g. `SF-01`).
   - The LLM observation schema produces qualitative string evidence (e.g., `value: "poor"`).
   - **Crucial Limitation Intentionally Implemented:** Because the frozen V2 `engine/` contains NO authoritative dictionary mapping strings to integers, the Feature Mapper explicitly refuses to map domains like `sleep`, `mood`, `stress`, `fear`, and `safety`. It does NOT hallucinate `Sleep = 3.0` from `sleep = poor`.
   - **Result:** These observations are preserved in `MedhaState.candidate_observations` for potential use by Question Engine triggers or LLM prompt history, but they do NOT bypass or contaminate the numeric feature vector.

2. **Valid Direct Mappings:**
   - `threat_event`: `"present" / "recent" / "yes"` maps to `Threat_Event = 1.0`, `"absent" / "none" / "no"` maps to `0.0`.
   - `recent_episode`: `"present"` maps to `Recent_Episode = 1.0`, `"absent"` maps to `0.0`.

3. **Conflict Resolution Policy:**
   - If `Threat_Event` or `Recent_Episode` already contains a valid float value in `state.structured_features` (e.g., populated by an active structured check-in), the conversational observation mapping is **skipped** (flagged as `rejected_structured_conflict`).
   - This ensures that authoritative structured answers always overwrite or prevent being overwritten by probabilistic conversational inference.

4. **Missingness:**
   - Missing features remain strictly `None`. Zero imputation is never used in the conversational layer.

## Verification

The new `DeterministicFeatureMapper` was injected into the `ConversationManager` via dependency injection. No code inside `engine/` was touched. 

Tests verify that `sleep="poor"` correctly yields `None` in `MedhaState.structured_features["Sleep"]`, while `threat_event="present"` yields `1.0`. All 79 chatbot tests pass, confirming perfect missingness preservation and modality independence.
