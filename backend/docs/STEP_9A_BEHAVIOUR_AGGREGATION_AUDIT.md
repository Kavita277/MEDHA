# Step 9A: Behaviour Aggregation Audit

## Files Inspected
- `backend/persistence/models/event.py` (RawEventModel schema)
- `backend/persistence/repositories/event.py` (EventRepository logic)
- `backend/services/event_service.py` (Event types and ingestion API)
- `backend/persistence/models/case.py` (Case definitions and timepoints)
- `backend/persistence/models/session.py` (Session definitions)
- User Prompt Instructions for Step 9A.

## Existing Event Structure
The `raw_events` table contains:
- `id` (uuid)
- `event_id` (string, unique for idempotency)
- `case_id` (uuid, foreign key)
- `session_id` (uuid, optional foreign key)
- `event_type` (string)
- `occurred_at` (datetime with timezone)
- `metadata_payload` (JSON)
- `created_at` (datetime)

## Existing Event Types
`session_start`, `session_end`, `screen_view`, `checkin_started`, `checkin_prompt_shown`, `checkin_answered`, `checkin_completed`, `chat_message_sent`, `journal_opened`, `journal_saved`, `voice_started`, `voice_completed`, `support_opened`, `notification_tapped`, `notification_dismissed`, `app_backgrounded`.

## Authoritative 10-Feature Definition
The aggregator is responsible for deterministically calculating:
1. `App_Interaction_Duration`
2. `App_Interaction_Duration_Deviation`
3. `Checkin_Response_Delay`
4. `Checkin_Response_Delay_Deviation`
5. `Checkin_Completion_Rate`
6. `Missed_Checkin_Count`
7. `Journal_Entry_Count`
8. `Chat_Message_Count`
9. `Late_Night_Usage_Ratio`
10. `Support_Resource_Access_Count`

## Ambiguities & Resolutions

### 1. Timepoint Mapping from `occurred_at`
**Ambiguity:** How does `occurred_at` map to a discrete integer `timepoint` if the bounds for a timepoint (e.g. Week 1 vs Week 2) are not persisted explicitly on the event? 
**Resolution:** The aggregator service interface `aggregate_case_timepoint(case_id, timepoint, start_time, end_time)` will accept explicit temporal bounds. Events whose `occurred_at` fall within `[start_time, end_time)` will belong to that timepoint. 

### 2. Late Night Timezone Configuration
**Ambiguity:** The time bounds for `Late_Night_Usage_Ratio` are not defined.
**Resolution:** We will define a configurable late-night window (e.g. 00:00 to 06:00) using UTC (unless events contain timezone-aware offsets). We will explicitly configure this in a `Config` class inside the aggregator to prevent magic numbers scattered in the code.

### 3. Missing Data vs Zero
**Ambiguity:** Should features like `App_Interaction_Duration` be `None` or `0.0` if no `session_start`/`session_end` pairs are found?
**Resolution:** If absolutely no app interaction events exist, duration is `None` (missing), allowing the ML pipeline to apply its median/mode imputation. If events exist but duration calculates to 0 (e.g. immediate close), it is `0.0`.

### 4. Baseline Window for Deviation
**Ambiguity:** How many past timepoints should be included in the historical baseline?
**Resolution:** The baseline will use the *mean* of all available prior timepoints for the case. T1 has no prior history, so T1 deviations will explicitly be `None` (cold start).
