# DEMO PIPELINE VERIFICATION REPORT (V2)

## PART 1 — DEMO TRACE SUMMARY

| Stage | Status | Evidence |
|------|--------|----------|
| Login | PASS | Token issued, Authentication successful |
| Session | PASS | Session `20935135-c703...` created and persisted |
| Chat | PASS | Dispatched to ConversationManager; generated response |
| Question Engine | PASS | Follow-up question `ES-01` correctly generated from context |
| Check-in | PASS | Checkin initialized (`SA-01` asked), answered with `8.0`, completed |
| State Persistence | PASS | `state_snapshot` successfully captures context |
| Text | PASS | Generated `Text_Pred: 30.1422` via BERT |
| Voice | PASS | Generated `Voice_Pred: 42.5286` via acoustic model |
| Behaviour | PASS | `behav_blocked: true`. `Behav_Pred` successfully handles as `null` |
| Structured | PASS | Generated `Struct_Pred: 35.398` |
| Fusion DDS | PASS | Produced `Fusion_DDS_Prediction: 36.1912` |
| Future Risk | PASS | Returns `null` appropriately due to insufficient longitudinal history (Timepoint 1) |
| Triage | PASS | Classified as `LOW` |
| Persistence | PASS | `PredictionResultModel` persisted to DB |
| Therapist API | PASS | `results_available: true` |

---

## PART 2 — THE PREDICTION TRACE

The pipeline successfully generated a partial-modality prediction by skipping the missing Behaviour model, without fabricating any numbers.

```text
Struct_Pred: 35.39820098876953
Text_Pred: 30.1422
Voice_Pred: 42.5286
Behav_Pred: null
Behav_Available: false
Fusion_DDS_Prediction: 36.191200256347656
Temporal_Risk_Score: null
Future_Escalation_Flag: null
Triage: LOW
```

## PART 3 — FIX IMPLEMENTATION NOTES

1. **Adapter Null Safety:** Fixed `backend/integrations/medha_v2.py` to defensively convert Python `None` into Pandas-compatible `np.nan` before DataFrame ingestion. This ensures mathematical operations (like `abs()`) in the frozen architecture evaluate safely instead of throwing TypeErrors.
2. **Modality Availability Adherence:** Modified `engine/v2/medha_v2_pipeline.py` to stop aggressively fabricating the `Behav_Available` flag as `1.0`. It now correctly reads the incoming `Behav_Available` flag.
3. **Pipeline Flag Extraction:** Updated `backend/services/prediction_service.py` to correctly extract the available modality flags (`struct_available`, `text_available`, `voice_available`) which are stored as top-level keys in the `state_snapshot`, allowing Text and Voice predictions to evaluate.

The architecture preserves the semantic meaning of missing data, ensuring the prototype is robust against unrecovered components!
