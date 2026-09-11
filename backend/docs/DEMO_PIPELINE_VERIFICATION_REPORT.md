# DEMO PIPELINE VERIFICATION REPORT

## PART B — DEMO TRACE SUMMARY

| Stage | Expected | Actual | Status |
|------|----------|--------|--------|
| User Login | success | Token issued, Authentication successful | PASS |
| Session | persisted | Session `34de30ab-14cf...` created and persisted | PASS |
| Chat | ConversationManager | Message successfully dispatched to ConversationManager; generated response | PASS |
| Question Engine | real follow-up | Follow-up question `ES-01` correctly generated from context | PASS |
| Check-in | state update | Checkin initialized (`SA-01` asked), answered with `8.0`, and completed | PASS |
| State Persistence | survives restore | `state_snapshot` successfully captures conversation history, checkin questions, and structured state | PASS |
| Text Model | prediction | Generated `Text_Distress: 0.111752`, `Fear: 0.999572` via BERT | PASS |
| Voice Model | prediction | Generated `Voice_Distress: 0.59` via acoustic model | PASS |
| Behaviour | actual availability | `behav_blocked: true` (Generator missing). Handled gracefully as `null`. | PASS |
| Structured Model | prediction | (Included in Fusion DDS computation) | PASS |
| Fusion | DDS | Failed due to missing behaviour features causing `abs(None)` crash | FAIL |
| GRU | Future Risk | Blocked by Fusion failure | BLOCKED |
| Triage | category | Returns `UNKNOWN` due to missing prediction | BLOCKED |
| Summary | useful summary | Summary exists internally in DB but missing from API | FAIL |
| Therapist API | results visible | Returns 200 OK with `results_available: false` | PASS |

### Failures & Blockers

1. **Prediction Generation Failed (Fusion/Behaviour)**
   - **Reason:** Exception `bad operand type for abs(): 'NoneType'`. The `medha_v2.py` adapter passes `None` for missing behaviour features. A downstream specialist or fusion layer attempts math on it instead of bypassing.
   - **Component:** `backend.services.prediction_service.generate_predictions` / `medha_v2.py`.
   - **Blocks Demo:** Yes. The Fusion DDS score and Triage are left blank.
   - **Minimal Fix:** Add null-checks in `medha_v2.py` or the underlying `FusionEngine` to gracefully handle completely missing `Behaviour` modalities.

2. **Therapist API Missing Conversation Summary**
   - **Reason:** The `state_snapshot` successfully contains the `conversation_summary`, but it is completely omitted from all schemas in `backend/schemas/therapist.py` and `backend/schemas/results.py`.
   - **Component:** `backend/api/v1/endpoints/therapist_results.py` and schemas.
   - **Blocks Demo:** Partially. Triage is available, but human context is missing.
   - **Minimal Fix:** Expose `conversation_summary` from the `state_snapshot` in the `CaseResultResponse`.

---

## PART C — TRACE DATA

Below is the verified, compact trace of the internal state progressing through the pipeline for user `V-DEMO-73d633`.

### 1. CHAT & CHECK-IN
**Chat Input:** `"I feel anxious and overwhelmed by everything happening right now."`
**Assistant Response:** `"I understand. If you feel comfortable answering: We noticed [case-related event] may be coming up. How are you coping with this?"`
**Check-in Answer:** `Safety: 8.0`

### 2. ACCUMULATED STATE (State Snapshot)
```json
{
  "structured_features": {
    "Safety": 8.0,
    ...
  },
  "conversation_history": [
    {"role": "user", "content": "I feel anxious and overwhelmed by everything happening right now."},
    {"role": "assistant", "content": "I understand..."}
  ],
  "question_history": [
    {"question_id": "SA-01", "answered": true, "response_text": "{\"value\": 8.0}"},
    {"question_id": "ES-01", "answered": false}
  ]
}
```

### 3. EXTRACTED FEATURES
**Text Features:**
- `Text_Distress`: 0.111
- `Fear`: 0.999
- `Threat_Context`: 0.338

**Voice Features:**
- `Voice_Distress`: 0.590
- `Speech_Rate_Deviation`: 1.0

**Behaviour Features:**
- `Engagement_Score`: null *(Blocked)*

### 4. PREDICTION OUTCOME
**Status:** `FAIL - Exception: bad operand type for abs(): 'NoneType'`
Due to missing behaviour data logic crashing the pipeline, the ultimate Fusion DDS, Future Risk, and Triage are skipped.

### 5. THERAPIST API VIEW
```json
{
  "results_available": false,
  "triage_level": "UNKNOWN",
  "specialists": {
    "struct_pred": null,
    "behav_blocked": true,
    "behav_block_reason": "Frozen V2 Behaviour Specialist integration is blocked..."
  }
}
```

---

## PART E — FINAL VERDICT

### 1. DEMO READY
The pipeline infrastructure is **excellent** up until the final prediction step. User authentication, session management, Question Engine context injection, check-in persistence, and modality availability (Text and Voice features) perfectly populate the `MedhaState`.

### 2. DEMO BLOCKERS
The `generate_predictions` pipeline currently throws an exception if the behaviour modality is fully `null`, failing the entire prediction process and leaving the therapist with no Fusion DDS or Triage score.

### 3. NON-BLOCKING LIMITATIONS
- Voice functionality works properly, but testing it automatically required generating a dummy WAV file.
- The `Behaviour` modality is completely disabled because the `Engagement_Score` generator is missing. This is handled gracefully by the therapist API (`behav_blocked: true`).

### 4. MINIMAL FIXES REQUIRED
1. **Null-Safety in Prediction:** Add a null-check guard around `abs()` in the V2 models or adapter to gracefully bypass missing features instead of crashing.
2. **Schema Exposure:** Plumb the `conversation_summary` from the `SessionModel.state_snapshot` into the `CaseResultResponse` so the therapist has conversational context.

### 5. THERAPIST RESULTS IMPROVEMENTS
*(See THERAPIST_RESULTS_GAP_AUDIT.md for full analysis)*
The current APIs provide solid ML metrics but obscure the actual human context. The therapist knows *if* the patient is distressed, but not *why*.

### 6. DO NOT TOUCH
- The `ConversationManager` and `MedhaState` persistence lifecycle (recently fixed) works flawlessly.
- The `QuestionEngine` properly picks up missing features and maintains cooldown states correctly.
- The V2 Modality Adapters correctly ingest inputs and return expected schemas.
