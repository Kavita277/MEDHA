# STEP 13 CHECK-IN INTEGRATION AUDIT

## 1. Existing Check-in Functionality
- **Models**: `CheckInModel`, `QuestionRecordModel`, and `CheckInStatus` already exist in `backend/persistence/models/checkin.py`.
- **Repository**: `CheckInRepository` exists in `backend/persistence/repositories/checkin.py` with CRUD methods.
- **Service**: `CheckInService` exists in `backend/services/checkin_service.py`. It implements `start_checkin`, `get_checkin`, and `submit_answer`.
- **API Endpoints**: `backend/api/v1/endpoints/checkins.py` has routes for `POST /sessions/{session_id}`, `GET /{checkin_id}`, and `POST /{checkin_id}/answer`.
- **Observation**: A large portion of Phase 1 to Phase 7 is already stubbed out or partially implemented.

## 2. Existing Question Engine API
- **Question Engine**: `DeterministicQuestionEngine` in `chatbot/engines/question_engine.py` is the frozen, authoritative engine that uses `engine/QuestionEngine/questions.json`.
- **Integration**: `CheckInService` instantiates `DeterministicQuestionEngine` and correctly delegates question selection to it via `select_next_question(medha_state)`. No logic is duplicated.

## 3. Existing State/Feature Update Mechanism
- **State**: The `MedhaState` architecture handles the structured features.
- **Update Mapping**: `CheckInService` maps answers to `medha_state` via `QUESTION_TO_FEATURE_MAP` and calls `medha_state.update_feature()`. This correctly preserves the distinction between missing values and zero.

## 4. Existing Event System
- **Event Schema/Service**: `backend/services/event_service.py` defines valid events (`checkin_started`, `checkin_answered`, `checkin_completed`, `checkin_prompt_shown`) and `RawEventModel` provides idempotent batch insertion.
- **Integration Gap**: `CheckInService.submit_answer` currently has a `TODO` for behavior events: `logger.info(f"Checkin event: checkin_submitted for session {session_obj.id}")`. It does not actually insert into `RawEventModel`. We need to use `EventRepository` to emit these natively from the service.

## 5. Existing User → Case → Session Ownership
- **Ownership Verification**: `CheckInService` uses `self.session_service.get_session_with_ownership_check(session_id, current_user)` to ensure the user has access to the session before proceeding. This is correct and robust.

## 6. Existing Authentication/RBAC
- **Auth Guard**: `backend/api/v1/endpoints/checkins.py` uses `Depends(get_current_user)` on all endpoints.

## 7. What Already Exists
- Database models and migrations (we need to verify if alembic migrations already exist for `checkins` table. They likely do since tests passed).
- `start_checkin`, `get_checkin`, and `submit_answer` workflows.
- `QuestionEngine` integration.
- RBAC and ownership isolation.

## 8. What Must Be Added
1. **Event Integration**: Update `CheckInService` to use `EventRepository` to emit:
   - `checkin_started`
   - `checkin_prompt_shown`
   - `checkin_answered`
   - `checkin_completed`
2. **Complete Checkin Route**: Implement `POST /api/v1/checkins/{checkin_id}/complete` and the corresponding service method.
3. **Idempotency Details**: We need to use UUIDv5 or similar for generating deterministic event IDs when emitting events from the backend to ensure idempotency.
4. **Step 13 Tests**: Write `backend/tests/test_step13_checkins.py`.

## 9. Compatibility Constraints
- Must not change the output format of `/events/batch` since Step 12 frontend relies on it.
- Must preserve the frozen V2 `MedhaState` structure and `QuestionEngine` output.

## 10. Explicit Confirmation
The frozen MEDHA V2 architecture, weights, feature order, scaler, fusion, GRU, and Question Engine logic will remain completely untouched. Step 10 remains intentionally BLOCKED.
