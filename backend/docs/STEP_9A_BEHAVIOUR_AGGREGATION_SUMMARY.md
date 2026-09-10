# Step 9A: Behaviour Aggregation Summary

## Architecture
The deterministic Behaviour Aggregator sits strictly between the `RawEventModel` (ingestion layer) and the `Behaviour Specialist` (inference layer). It transforms raw chronological logs into the required 10 authoritative behaviour features per `(case_id, timepoint)`. These features are persisted into the `BehaviourFeatureSnapshotModel` table to support efficient lookups and caching, with a deterministic recalculation policy driven by bounds `[start_time, end_time)`.

## Files Created / Modified
- **Created**: `backend/persistence/models/behaviour_snapshot.py` (Feature persistence schema)
- **Modified**: `backend/persistence/models/__init__.py` (Export model)
- **Created**: `ead3432ccad1_add_behaviour_feature_snapshots_table.py` (Alembic migration)
- **Created**: `backend/services/behaviour/schemas.py` (Internal DTOs representing the exact 10 features)
- **Created**: `backend/services/behaviour/event_mapping.py` (Pure functions converting chronological event streams into basic metrics)
- **Created**: `backend/services/behaviour/baseline.py` (Baseline and deviation algorithms)
- **Created**: `backend/services/behaviour/feature_aggregator.py` (The orchestrator)
- **Created**: `backend/tests/test_behaviour_aggregator.py` (Verification suite)

## Event -> Feature Mapping & 10 Features
1. **App_Interaction_Duration**: Derived chronologically by matching `session_start` to `session_end` events. Unmatched starts are ignored (missing data). 
2. **App_Interaction_Duration_Deviation**: Current Duration minus Baseline.
3. **Checkin_Response_Delay**: Calculated as average duration between `checkin_prompt_shown` and `checkin_completed`. Note: The authoritative completion event in Step 8 is `checkin_completed`, not `checkin_submitted`.
4. **Checkin_Response_Delay_Deviation**: Current Delay minus Baseline.
5. **Checkin_Completion_Rate**: `completed_checkins / prompts_shown`.
6. **Missed_Checkin_Count**: Counts check-ins that were prompted but overridden by a new prompt.
7. **Journal_Entry_Count**: Extracted from `journal_saved` events. Deduplicated by `journal_id` payload metadata if present.
8. **Chat_Message_Count**: Extracted from `chat_message_sent` where payload role is `user`.
9. **Late_Night_Usage_Ratio**: Counts subset of interactions occurring within the dynamically configured `BEHAVIOUR_LATE_NIGHT_START_HOUR` and `BEHAVIOUR_LATE_NIGHT_END_HOUR` utilizing the `BEHAVIOUR_LATE_NIGHT_TIMEZONE` config.
10. **Support_Resource_Access_Count**: Derived from `support_opened` or `support_resource_accessed`.

## Timepoint Definition
Handled explicitly via API parameter alongside exact datetime `[start_time, end_time)` bounds, providing flexibility for the domain caller to define what temporal window constitutes a "timepoint" (e.g. 7 days).

## Baseline Definition & Missing-Data Behavior
- **Baseline**: The mean of the target feature across all explicitly past timepoints (T < current_timepoint).
- **Temporal Leakage**: Strict tests prove that future events (or timepoints) never impact historical baseline deviation calculations.
- **Missing Data (Cold-Start)**: At `timepoint=1`, baselines do not exist. Features relying on deviation evaluate to `None`. 
- **Missing Data vs Zero Activity**: A timepoint containing zero interaction events yields `None` for counts/duration. A timepoint containing events (e.g., chat) but no journal saves evaluates to `0.0` for `Journal_Entry_Count`. Missing values (`None`) inform MEDHA V2 that median imputation is necessary, whereas `0.0` implies verified absence of behavior.

## Late Event Handling & Idempotency
- **Late events**: Supplying explicit temporal boundaries ensures that out-of-order ingestion handles events properly based on their `occurred_at`. 
- **Reaggregation**: Running `aggregate_case_timepoint` again for an old timepoint will successfully recalculate it.
- **Idempotency**: Events inside a query window are inherently deduplicated by `event_id` prior to algorithm processing, avoiding duplicate metric inflation.

## Known Limitations
- "Missed" checkins currently only count if a new prompt explicitly overrides the old prompt. A timed timeout logic may be necessary depending on frontend implementations.

## Frozen Components
- No components within `engine/`, `chatbot/`, or V2 inference were modified or touched.
- The Behaviour Specialist and Fusion were NOT implemented.

## Test Results
`pytest backend/tests/test_behaviour_aggregator.py` passes 5/5 tests demonstrating temporal leakage protection, accurate deviations, missing vs zero logic, and idempotency. The full backend test suite passes 74/74.

## Next Integration Point
Step 10: Injecting these 10 authoritative behaviour features into the V2 `Behaviour Specialist` Ridge Regression model to generate `Behav_Pred`.

STEP 9A READY FOR STEP 10
