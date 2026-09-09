# MEDHA Chatbot — Step 9A Correction Report

**STEP 9A STATUS: PASS**

## 1. Objective
Correct the Step 9 Conversation Summary implementation to handle deterministic contradictions, supersession, historical preservation, and provenance tracking without mutating or violating the strict boundaries of the frozen MEDHA V2 predictive pipeline.

## 2. Problem Found
The original Step 9 implementation had bounded storage (max 10 items per category) and prevented exact duplicate entries, but it did not actually implement deterministic contradiction or supersession handling. If a user updated a statement (e.g., from "I am sleeping well" to "I am not sleeping well"), the system merely appended the new fact, leaving the old one as "active". Additionally, provenance was hardcoded such that `source="llm_extraction"`, conflating the original source of the information (the user) with the extraction mechanism (the LLM).

## 3. Work Completed
- **Contradiction & Supersession Handling:** Updated the `ConversationSummaryEngine` to instruct the LLM to provide structured JSON updates containing both the new content and the exact string of the older content it supersedes. If an explicit update is detected, the engine deterministically locates the older item and changes its status from `"active"` to `"superseded"`.
- **Ambiguous Updates:** If the LLM proposes a supersession but the old item isn't found (or if it's ambiguous), the engine safely marks the new item as `"unresolved"`.
- **Historical Preservation:** Superseded items are *never deleted*. They remain in the summary lists (up to the category capacity limit), ensuring the `MedhaState` naturally preserves historical changes over time without requiring redundant tracking mechanisms.
- **Provenance Correction:** Refactored the `SummaryItem` schema. It now explicitly defaults to `source="user_statement"` (the origin of the fact) and uses the newly added `extracted_by="llm_extraction"` to specify the mechanism. Original user messages are preserved in the `evidence` field.
- **Safety Isolation:** Maintained strict isolation; the summary engine updates state *after* the Step 8 `DeterministicSafetyGateway` processes candidate observations, ensuring the summary context cannot override emergency routing.
- **V2 Isolation:** Verified through testing that extracting semantic facts (like "poor sleep") does not mutate numerical values in `state.structured_features["Sleep"]`.

## 4. Files Created/Modified

**Created:**
- `chatbot/docs/MEDHA_CHATBOT_STEP9A_CORRECTION_REPORT.md`

**Modified:**
- `chatbot/summary/summary_schema.py`
- `chatbot/summary/conversation_summary_engine.py`
- `chatbot/tests/test_conversation_summary.py`

**Untouched:**
- `engine/` = UNTOUCHED
- `chatbot/state/medha_state.py` (No schema changes were necessary aside from the `SummaryItem` definition)
- `chatbot/conversation_manager.py` (Integration flow remained correct)

## 5. Data Flow
```
User message
    ↓
ConversationManager
    ↓
Safety Gateway (Step 8)
    ↓
LLM Provider Hook
    ↓
Summary Engine Hook (Step 9A)
    |-- Asks LLM for structured NEW updates + supersedes_content
    |-- LLM returns {"content": "...", "supersedes_content": "..."}
    |-- Engine locates old item -> sets status="superseded"
    |-- Engine appends new item -> sets status="active"
    |-- Engine sets source="user_statement", extracted_by="llm_extraction", evidence=message
    ↓
ConversationSummary updated
    ↓
ConversationManager completes turn
```

## 6. Provenance Model
- **`source`**: The origin of the information. Defaults to `"user_statement"`.
- **`extracted_by`**: The mechanism that populated the schema. Set to `"llm_extraction"`.
- **`evidence`**: The exact user message string that triggered the extraction.

## 7. Contradiction Rules
- **`active`**: The default status for newly appended, uncontested information.
- **`superseded`**: Assigned strictly when the LLM identifies explicit update language (e.g., "actually", "but now") and the exact prior content string is found in the summary list.
- **`unresolved`**: Assigned when a contradiction is proposed but the prior item cannot be precisely located, or when the relationship is ambiguous.

## 8. V2 Isolation
The test `test_v2_boundary_isolation` confirms that updates to the summary do not directly mutate `MedhaState.structured_features`. The summary acts purely as conversational memory.

## 9. Safety Isolation
The summary engine does not replace or override the `DeterministicSafetyGateway`. It merely records context, while emergency triage remains deterministic and prior to summary updates.

## 10. Tests
```bash
python -m pytest chatbot/tests/ -v
# Result: 98 passed, 0 failures

python -m pytest engine/tests/ -v
# Result: 224 passed, 0 failures
```

**New Tests Added:**
- `test_explicit_update` (Test 1 & 2)
- `test_ambiguous_contradiction` (Test 3)
- `test_provenance_and_deduplication` (Test 4 & 5)
- `test_v2_boundary_isolation` (Test 6)
- `test_bounded_memory` (Test 8)

## 11. Limitations
The contradiction system relies on exact string matching against the LLM's proposed `supersedes_content`. It does not perform vector-based semantic similarity to find loosely related contradictions. This is an intentional design choice to favor preserving ambiguous information over incorrectly deleting or overriding it.

## 12. Compliance Checklist
- [x] No engine files modified
- [x] No model checkpoints modified
- [x] No new risk model
- [x] No new fusion
- [x] No new GRU
- [x] No DDS changes
- [x] No V2 schema changes
- [x] No hallucinated numeric mappings
- [x] Historical information preserved
- [x] Explicit updates handled deterministically
- [x] Provenance preserved
- [x] Safety Gateway remains authoritative
- [x] All tests pass

**STEP 9A STATUS: PASS**
