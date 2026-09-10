# Step 9 Walkthrough: Behaviour Event Ingestion

We have successfully implemented the MVP Behavior Event Ingestion layer, allowing the MEDHA application to ingest structured telemetry and behavior events idempotently, while strictly maintaining patient-case isolation.

## Changes Made

1. **Database Modeling**
   - Created `RawEventModel` spanning `event_id`, `case_id`, `session_id`, `event_type`, `occurred_at`, and `metadata_payload`.
   - Generated the Alembic migration `efe33f56db5e_add_raw_events_table` and successfully applied it to the database (`alembic upgrade head`).

2. **Persistence and Service Layer**
   - Implemented `EventRepository.batch_insert_idempotent()`. This method uses nested transactions (with `IntegrityError` catching) to ensure that if a client retries a batch with the same `event_id`, the duplicate is safely ignored without failing the whole batch.
   - Built `EventService.process_batch()` to evaluate patient ownership (`case_id`) and roles (User vs. Therapist) before routing validated events to the repository.

3. **API Implementation**
   - Defined `EventBatchRequest` and `EventBatchResponse` schemas.
   - Created the `POST /api/v1/events/batch` endpoint.
   - Integrated the new `/events` router into the V1 core router (`backend/api/v1/router.py`).

4. **Testing**
   - Implemented integration tests simulating Patients pushing telemetry events and malicious cross-patient (and cross-therapist) access attempts.
   - All tests successfully pass and duplicate retries confirm `ignored_duplicate_count = 1`.

## Validation Results

- `pytest backend/tests/test_event_ingestion.py` — **3/3 passed**

> [!TIP]
> The ingestion layer is now functional for all specified event schemas (e.g. `session_start`, `screen_view`, `voice_completed`, etc.) natively without relying on any behaviour extraction scripts yet.
