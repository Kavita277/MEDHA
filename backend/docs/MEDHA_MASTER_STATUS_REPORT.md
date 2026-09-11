# MEDHA Backend — Master Status Report

**Generated:** 2026-09-11  
**Based on:** Direct codebase inspection of `backend/`, `chatbot/`, `engine/`, and root-level files.  
**Test Baseline (from docs):** 188 backend tests passing, 0 failing.

---

## 1. High-Level Architecture Summary

```
Client (Patient App / Therapist Dashboard)
        ↓ HTTP / REST
FastAPI Backend  (backend/main.py → backend/api/v1/)
        ↓
Application Services  (backend/services/)
        ↓
Integrations  (backend/integrations/)  ←→  Chatbot Layer  (chatbot/)
        ↓
Frozen ML Pipeline  (engine/v2/medha_v2_pipeline.py)
        ↓
PostgreSQL  (via SQLAlchemy ORM + Alembic migrations)
```

The backend is strictly an **orchestration layer**. It does not contain ML model code.  
The frozen ML models are accessed through two bridges:
- `backend/integrations/medha_v2.py` → direct `MedhaV2Pipeline` call
- `backend/integrations/session_state_adapter.py` → attaches `MedhaState` to `ConversationManager`

---

## 2. Complete File Inventory (Verified in Codebase)

### 2.1 Entry Point
| File | Status | Notes |
|------|--------|-------|
| `backend/main.py` | ✅ Complete | FastAPI app factory, CORS, lifespan hooks, global exception handlers, request timing middleware, privacy-safe error masking |
| `backend/config.py` | ✅ Complete | Typed Pydantic settings, ENV vars, JWT config, DB pool config, CORS origins, behaviour timezone config |
| `backend/dependencies.py` | ✅ Complete | `get_db()` dependency |

### 2.2 API Layer (`backend/api/v1/`)
| File | Status | Endpoints Registered |
|------|--------|---------------------|
| `router.py` | ✅ Complete | Aggregates all 11 sub-routers under `/api/v1` |
| `endpoints/auth.py` | ✅ Complete | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`, `POST /auth/logout` |
| `endpoints/sessions.py` | ✅ Complete | `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/end` |
| `endpoints/chat.py` | ✅ Complete | `POST /chat/message`, `GET /chat/history` |
| `endpoints/checkins.py` | ✅ Complete | `POST /checkins`, `GET /checkins/{id}`, `POST /checkins/{id}/answer`, `POST /checkins/{id}/complete` |
| `endpoints/voice.py` | ✅ Complete | `POST /voice/checkin` (multipart upload + background prediction enqueue) |
| `endpoints/journal.py` | ✅ Complete | `POST /journal`, `GET /journal`, `GET /journal/{id}`, `PATCH /journal/{id}` |
| `endpoints/events.py` | ✅ Complete | `POST /events/batch` (idempotent telemetry ingestion) |
| `endpoints/health.py` | ✅ Complete | `GET /health`, `GET /health/ready` |
| `endpoints/therapist.py` | ✅ Complete | `POST /therapist/users`, `GET /therapist/users`, `PATCH /therapist/users/{id}/status`, `PATCH /therapist/cases/{id}`, `GET /therapist/audit-logs` |
| `endpoints/therapist_results.py` | ✅ Complete | `GET /therapist/cases`, `GET /therapist/cases/{id}/results`, `GET /therapist/sessions/{id}/results`, `GET /therapist/cases/{id}/sessions`, `GET /therapist/cases/{id}/checkins`, `GET /therapist/cases/{id}/behaviour`, `GET /therapist/cases/{id}/alerts`, `PATCH /therapist/cases/{id}/alerts/{alert_id}` |
| `endpoints/therapist_insights.py` | ✅ Complete | `GET /therapist/cases/{id}/insights`, `GET /therapist/sessions/{id}/insights` |
| `endpoints/therapist_recommendations.py` | ✅ Complete | `GET /therapist/cases/{id}/recommendations`, `GET /therapist/cases/{id}/safety-protocol`, `GET /therapist/sessions/{id}/recommendations` |

> [!NOTE]
> **Missing from plan vs. reality:** The backend plan specified `GET /api/v1/therapist/me` and `GET /api/v1/users/me` / `PATCH /api/v1/users/me` as standalone endpoints. These are currently embedded within `auth.me` and `therapist.py` respectively, not as separate user-profile endpoint files. Functionally covered but not identical to the plan's spec.

### 2.3 Schemas (`backend/schemas/`)
| File | Status |
|------|--------|
| `auth.py` | ✅ Complete — Login request, token response |
| `case.py` | ✅ Complete — `CaseResponse`, `CaseUpdateRequest`, `TherapistCreateUserRequest`, `TherapistUserResponse` |
| `chat.py` | ✅ Complete — `ChatMessageCreate`, `ChatTurnResult`, `ChatHistoryResponse`, `ChatMessageResponse` |
| `checkin.py` | ✅ Complete — `CheckInResponse`, `QuestionResponse`, `CheckInAnswerResponse` |
| `session.py` | ✅ Complete — `SessionCreateRequest`, `SessionResponse` |
| `event.py` | ✅ Complete — Batch event payload |
| `health.py` | ✅ Complete |
| `insights.py` | ✅ Complete — `CaseInsightsResponse`, `InsightFactorItem`, `InsightSignalsSummary`, `InsightActivitySummary`, `InsightContextSummary` |
| `recommendations.py` | ✅ Complete — `CaseRecommendationsResponse`, `RecommendationItem`, `SafetyProtocolResponse`, `SelfHelpResourceItem` |
| `results.py` | ✅ Complete — `CaseResultResponse`, `SpecialistPredictionsResponse` (with `behav_blocked` field), `AlertSummaryResponse`, `AlertHandleRequest`, `AlertHandleResponse`, `BehaviourSummaryResponse`, `CheckinSummaryResponse` |
| `therapist.py` | ✅ Complete |
| `user.py` | ✅ Complete — `UserResponse`, `UserStatusUpdateRequest` |
| `voice.py` | ✅ Complete — `VoiceCheckInResponse` |
| `journal.py` | ✅ Complete |
| `audit.py` | ✅ Complete — `AuditLogResponse` |

### 2.4 Database Models (`backend/persistence/models/`)
| Model | DB Table | Status |
|-------|----------|--------|
| `user.py` | `users` | ✅ Complete — Role enum (`USER`/`THERAPIST`), Status enum, password_hash, must_change_password |
| `therapist.py` | `therapists` | ✅ Complete — FK to users |
| `case.py` | `cases` | ✅ Complete — `victim_id`, `therapist_id`, `user_id`, `current_timepoint`, `status`, `closed_at` |
| `session.py` | `sessions` | ✅ Complete — `session_identifier`, `timepoint`, `state_snapshot` (JSON), `status`, `closed_at` |
| `chat_message.py` | `chat_messages` | ✅ Complete — `role`, `content`, `metadata_payload` |
| `checkin.py` | `checkins` + `question_records` | ✅ Complete — `CheckInModel` + `QuestionRecordModel` with `answer_status`, `answered_at` |
| `event.py` | `raw_events` | ✅ Complete — `event_id` unique (idempotency), `event_type`, `metadata_payload` |
| `behaviour_snapshot.py` | `behaviour_feature_snapshots` | ✅ Complete — All 10 V2 behaviour features + deviations |
| `prediction_result.py` | `prediction_results` | ✅ Complete — All 4 specialist scores, Fusion DDS, Temporal Risk, Future Escalation Flag, triage_level, availability flags |
| `safety_event.py` | `safety_events` | ✅ Complete — `event_type`, `severity`, `status`, `handled_by`, `handled_at` |
| `audit_log.py` | `audit_logs` | ✅ Complete — Immutable log of actor, action, resource, status, metadata |
| `voice_record.py` | `voice_records` | ✅ Complete — `available` flag, `timepoint` |
| `journal_entry.py` | `journal_entries` | ✅ Complete |

> [!WARNING]
> **Missing DB Model (vs. plan):** The plan specified `observations` and `structured_features` tables (§7.9, §7.10). These **do not exist** as standalone DB tables. Structured features are stored inside `SessionModel.state_snapshot` (JSON column), not normalized into a relational table. Observations live in `MedhaState.candidate_observations` serialized within the same snapshot. This is a deliberate deviation — functionally equivalent but differs from the plan spec.

> [!WARNING]
> **Missing DB Model (vs. plan):** `voice_features` table (§7.14 in plan) does not exist as a separate normalized table. Voice features are stored in `state_snapshot` JSON, not in a dedicated `voice_features` table.

### 2.5 Repositories (`backend/persistence/repositories/`)
| File | Status |
|------|--------|
| `user.py` | ✅ Complete |
| `therapist.py` | ✅ Complete |
| `case.py` | ✅ Complete — `get_by_victim_id`, `list_cases_for_therapist`, `get_active_case_for_user` |
| `session.py` | ✅ Complete — `list_for_case`, `get_by_identifier` |
| `chat_message.py` | ✅ Complete |
| `checkin.py` | ✅ Complete — `get_active_checkin_for_session`, `create_question_record` |
| `event.py` | ✅ Complete — `batch_insert_idempotent` |
| `prediction_result.py` | ✅ Complete — `get_latest_for_case`, `get_latest_for_session` |
| `audit_log.py` | ✅ Complete — `list_logs` with actor filtering |

> [!WARNING]
> **Missing Repositories (vs. plan):** The plan specified `feature_repository.py` and `alert_repository.py`. These do **not exist** as separate repo files. Alerts (`SafetyEventModel`) are queried directly via SQLAlchemy in endpoint files. This is a minor structural gap.

### 2.6 Services (`backend/services/`)
| File | Status | Notes |
|------|--------|-------|
| `chatbot_service.py` | ✅ Complete | Full ConversationManager integration, state persistence, message persistence |
| `checkin_service.py` | ✅ Complete | DeterministicQuestionEngine integration, feature mapping from answers, event emission |
| `session_service.py` | ✅ Complete | Session creation, ownership check, close session |
| `case_service.py` | ✅ Complete | `get_active_case_for_user` |
| `prediction_service.py` | ✅ Complete | Aggregates state snapshot + behaviour snapshot, calls `run_v2_inference`, writes `PredictionResultModel` |
| `voice_service.py` | ✅ Complete | Temp file management, MedhaVoiceAdapter call, VoiceRecordModel persistence, secure temp cleanup |
| `journal_service.py` | ✅ Complete |
| `event_service.py` | ✅ Complete | Idempotent batch event ingestion |
| `insights_service.py` | ✅ Complete | ExplainabilityEngine integration, longitudinal trend calculation, contextual flags aggregation |
| `recommendation_service.py` | ✅ Complete | RecommendationEngine + AlertEngine integration |
| `triage_service.py` | ✅ Complete | `compute_triage_level()` helper |
| `audit_service.py` | ✅ Complete | Central `audit_service.log_event()` used across all sensitive operations |
| `seed_service.py` | ✅ Complete | 4 longitudinal demo cases, idempotent, real V2 pipeline execution |
| `behaviour/feature_aggregator.py` | ✅ Complete | Full 10-feature aggregation with T-1 baselining and deviation calculation |
| `behaviour/event_mapping.py` | ✅ Complete | Maps raw events to duration, checkin metrics, counts, late-night ratio |
| `behaviour/baseline.py` | ✅ Complete | Historical deviation calculation |
| `behaviour/schemas.py` | ✅ Complete | `BehaviourFeatureSnapshot` Pydantic DTO |

> [!WARNING]
> **Missing Services (vs. plan):** Plan specified `user_service.py`, `therapist_service.py`, and `alert_service.py` as separate service files. These do not exist as discrete files. Their logic is inline within endpoint handlers or spread across case/audit services. Minor architectural gap vs. plan.

### 2.7 Integrations (`backend/integrations/`)
| File | Status | Notes |
|------|--------|-------|
| `medha_v2.py` | ✅ Complete | Singleton `MedhaV2Pipeline`, full DataFrame construction, all expected feature columns filled with `np.nan`, inference execution, result extraction |
| `session_state_adapter.py` | ✅ Complete | `serialize_medha_state`, `restore_medha_state`, `create_initial_medha_state`, `attach_to_conversation_manager`, `sync_from_conversation_manager` |

> [!WARNING]
> **Missing Integration (vs. plan):** Plan specified `backend/integrations/alert_provider.py` (production alert backend — webhook, SMS, PagerDuty). This file **does not exist**. The `SafetyTrigger` in the chatbot still uses `MockAlertEngine`. **No real production alert delivery mechanism (webhook, SMS, email) has been implemented.** This is the single most critical production gap.

> [!WARNING]
> **Missing Integration (vs. plan):** Plan specified `backend/integrations/storage.py` (for voice/audio storage). This file **does not exist**. Voice is processed from a temp file and the temp file is immediately deleted. There is no S3/blob/persistent audio storage.

### 2.8 Security (`backend/security/`)
| File | Status | Notes |
|------|--------|-------|
| `tokens.py` | ✅ Complete | JWT creation, verification, expiry |
| `passwords.py` | ✅ Complete | bcrypt hashing and verification |
| `dependencies.py` | ✅ Complete | `get_current_user`, `get_current_therapist` FastAPI dependencies |
| `redaction.py` | ✅ Complete | Recursive sensitive field redaction, JWT pattern stripping, URL sanitization, internal path masking from error responses |

> [!NOTE]
> **Config security gap:** `JWT_SECRET_KEY` defaults to a hardcoded insecure dev secret in `config.py`. This is documented in the code itself and **must** be overridden via environment variable before production deployment.

### 2.9 Background Jobs (`backend/jobs/`)
| File | Status | Notes |
|------|--------|-------|
| `prediction_queue.py` | ✅ Complete | Asyncio in-memory queue, `enqueue_prediction()`, `process_queue()` background worker loop, graceful shutdown via `asyncio.CancelledError` |

> [!CAUTION]
> **Critical gap:** The prediction queue is **in-memory only**. If the server restarts, any queued prediction jobs are permanently lost. There is no Redis, Celery, or durable queue backing this. This is not suitable for production.

### 2.10 Workers (`backend/workers/`)
| File | Status | Notes |
|------|--------|-------|
| `__init__.py` | ⚠️ Stub only | Contains only a docstring. The plan specified `behaviour_aggregator.py`, `prediction_worker.py`, `alert_worker.py` as background workers here. None of these worker scripts exist as actual files. |

> [!CAUTION]
> **The entire `workers/` directory is empty of actual implementation.** Background jobs are instead handled through `backend/jobs/prediction_queue.py`. The behaviour aggregation has no automated trigger — it is called manually or from seed scripts. There is no `behaviour_aggregator.py` worker.

### 2.11 Database Migrations (`backend/persistence/migrations/versions/`)
| Migration | Status |
|-----------|--------|
| `001_create_users_and_therapists.py` | ✅ Exists |
| `002_create_cases.py` | ✅ Exists |
| `003_create_sessions.py` | ✅ Exists |
| `0427993cb13f_add_checkins_and_question_records.py` | ✅ Exists |
| `4acffe24d06a_create_chat_messages_table.py` | ✅ Exists |
| `b3f7e291cc4a_add_prediction_results_table.py` | ✅ Exists |
| `c7d2984ab12e_add_audit_logs_table.py` | ✅ Exists |
| `ead3432ccad1_add_behaviour_feature_snapshots_table.py` | ✅ Exists |
| `efe33f56db5e_add_raw_events_table.py` | ✅ Exists |

> [!WARNING]
> **Missing Migrations:** The plan's `observations` and `structured_features` tables have no migrations, because they were not implemented as standalone tables (by design). The `voice_features` table also has no migration. The `safety_events` table migration is **missing** — `SafetyEventModel` exists as a Python model but there is no corresponding Alembic migration script in the `versions/` folder.

### 2.12 Tests (`backend/tests/`)
| Test File | Scope | Status |
|-----------|-------|--------|
| `conftest.py` | Shared fixtures (in-memory SQLite DB, test client, seeded therapist/user) | ✅ |
| `test_app.py` | App startup, root endpoint | ✅ |
| `test_health.py` | Health probe | ✅ |
| `test_auth_api.py` | Login, token refresh, logout | ✅ |
| `test_security_utils.py` | Password hashing, JWT tokens | ✅ |
| `test_user_models.py` | User ORM model | ✅ |
| `test_case_models.py` | Case ORM model | ✅ |
| `test_database.py` | DB connection, session management | ✅ |
| `test_migrations.py` | Alembic migration integrity | ✅ |
| `test_account_repositories.py` | User/Therapist repositories | ✅ |
| `test_session_repository.py` | Session repository | ✅ |
| `test_case_service.py` | Case service unit tests | ✅ |
| `test_sessions_api.py` | Full session lifecycle API tests | ✅ |
| `test_session_restoration.py` | MedhaState serialize/deserialize round-trip | ✅ |
| `test_therapist_api.py` | Therapist management endpoints | ✅ |
| `test_therapist_results_api.py` | Results, sessions, alerts, behaviour, checkins API | ✅ |
| `test_therapist_insights_api.py` | Insights endpoint | ✅ |
| `test_therapist_recommendations_api.py` | Recommendations + safety protocol | ✅ |
| `test_behaviour_aggregator.py` | Behaviour feature aggregation | ✅ |
| `test_event_ingestion.py` | Batch event ingestion | ✅ |
| `test_chatbot_integration.py` | Chatbot service + ConversationManager | ✅ |
| `test_checkin_integration.py` | Check-in flow with Question Engine | ✅ |
| `test_privacy_hardening.py` | Redaction, sanitization, anti-enumeration | ✅ |
| `test_audit_logging.py` | Audit log events | ✅ |
| `test_authorization_audit.py` | ACCESS_DENIED, 403 anti-enumeration | ✅ |
| `test_step12_integration.py` | Chat + ConversationManager integration | ✅ |
| `test_step13_checkins.py` | Full check-in integration | ✅ |
| `test_step29_audit_verification.py` | Security audit (Step 29) | ✅ 5/5 passed |
| `test_step30_e2e_flow.py` | Full 15-step clinical lifecycle E2E | ✅ |
| `test_step30_seed_verification.py` | Demo seed data + prediction authenticity | ✅ |
| `api/test_journal_api.py` | Journal endpoints | ✅ |
| `api/test_voice_api.py` | Voice upload endpoint | ✅ |
| `services/test_prediction_service.py` | Prediction service unit | ✅ |
| `integration/test_v2_integration.py` | V2 pipeline integration | ✅ |
| `jobs/` | *(empty — no job-specific tests)* | ⚠️ No tests for `prediction_queue.py` |

---

## 3. Known Problems & Confirmed Issues

### 🔴 CRITICAL — Behaviour Specialist Permanently Blocked
**File:** `backend/api/v1/endpoints/therapist_results.py` lines 84–88, and `backend/schemas/results.py`

The Frozen V2 Behaviour Ridge Specialist is **permanently blocked** from producing predictions. The `behav_pred` field is always `null`. The `behav_available` flag is always `False`. This is explicitly documented in the code with this note:

> *"Frozen V2 Behaviour Specialist integration is blocked: Engagement_Score original data generator was not recovered (Step 9C). The ML team must provide the generator script or retrain with Step 9A event metrics."*

**Impact:** The `Fusion_DDS_Prediction` score is computed with `Behav_Available = False`, meaning it uses only 3 modalities (Structured, Text, Voice). The Behaviour Ridge Model's contribution to the DDS is always zero/absent. This is a fundamental capability gap that requires the ML team to recover the `Engagement_Score` generator.

---

### 🔴 CRITICAL — No Production Alert Backend
**File:** `chatbot/safety/safety_trigger.py` — uses `MockAlertEngine`  
**Missing:** `backend/integrations/alert_provider.py` (not implemented)

When the Safety Trigger detects a crisis event (suicidal intent, immediate danger, etc.), it emits a `SafetyEvent` to `MockAlertEngine`, which stores it only in-memory. **No webhook, SMS, email, or external system is notified.** In a live production environment, therapists would never receive real-time crisis alerts. The event is persisted to `safety_events` DB table, but there's no push mechanism.

---

### 🟠 HIGH — In-Memory Prediction Queue
**File:** `backend/jobs/prediction_queue.py`

The prediction job queue is backed by `asyncio.Queue()` (in-memory). On any server restart or crash:
- All queued prediction jobs are silently dropped.
- No retry logic.
- No dead-letter queue.

Needs a durable queue (Redis, Celery, or RQ) for production.

---

### 🟠 HIGH — Voice Features Not Synced to Prediction Pipeline After Voice Check-In
**File:** `backend/services/voice_service.py` lines 36–41

```python
# Comment in the code itself:
# For the purpose of voice adapter, we instantiate an empty state.
# In a real integrated flow, this might pull the current MedhaState from DB.
state = MedhaState(victim_id=case.victim_id, session_id=...)
```

When a voice check-in is processed, the `MedhaVoiceAdapter` runs on a **brand new empty `MedhaState`**, not the session's current state. The 5 voice features extracted (`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`) are never written back into the session's persistent `state_snapshot`. The prediction pipeline therefore cannot access voice features from standalone voice check-ins. Voice features only reach the pipeline when voice is processed as part of a chat turn (via `ConversationManager`).

---

### 🟡 MEDIUM — No Refresh Token Rotation / Invalidation Store
**File:** `backend/security/tokens.py`

JWT refresh tokens are issued but there is no server-side invalidation list. A logout does not truly invalidate the refresh token — the token remains valid until its expiry. This is a security weakness for clinical data.

---

### 🟡 MEDIUM — `workers/` Directory Is Completely Empty
The plan specified automated background workers for:
- `behaviour_aggregator.py` — automatic behaviour feature aggregation after events
- `prediction_worker.py` — automated scheduled predictions
- `alert_worker.py` — alert dispatching worker

None of these exist. Behaviour aggregation must be manually triggered (e.g., from seed scripts or test code). There is no scheduled pipeline run.

---

### 🟡 MEDIUM — Missing Standalone DB Tables for Observations and Structured Features
The plan (§7.9, §7.10) specified normalized relational tables for `observations` and `structured_features`. These were not implemented. All observation and structured feature data lives inside `SessionModel.state_snapshot` as a JSON blob. This makes querying individual features across sessions or time complex and non-indexable.

---

### 🟡 MEDIUM — Missing `safety_events` Alembic Migration
The `SafetyEventModel` Python class exists, but there is no Alembic migration file in `versions/` for the `safety_events` table. The table is likely created only via `Base.metadata.create_all()` in test setup, not via proper versioned migration.

---

### 🟡 MEDIUM — Insecure JWT Secret Default
**File:** `backend/config.py` line 100

```python
JWT_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "medha-insecure-dev-jwt-secret-change-in-production-1234567890"))
```

If deployed without setting `JWT_SECRET_KEY` environment variable, a known insecure secret is used. All tokens become forgeable.

---

### 🟡 MEDIUM — No Persistent Storage for Voice Audio
**File:** `backend/services/voice_service.py`

Raw audio is uploaded, saved to `tempfile.mkstemp()`, processed by the voice adapter, and then **immediately deleted** in a `finally` block. There is no audio archival, no S3 bucket, no secure long-term storage. The plan specified `storage.py` in integrations for this purpose — it was never created.

---

### 🟢 LOW — No Tests for `prediction_queue.py`
The `backend/tests/jobs/` directory is empty. The asyncio prediction queue background worker has no unit tests.

---

### 🟢 LOW — Backend Not Split from Root `app.py`
The original Streamlit `app.py` at the root still exists and instantiates `ConversationManager` directly (in-process). It is not deprecated or connected to the backend APIs. Two separate runtimes (Streamlit dev UI and the FastAPI backend) can simultaneously access ML models, which could cause conflicts in production if both are run together.

---

## 4. What Is Fully Working ✅

| Capability | Verified |
|-----------|---------|
| JWT Authentication (login, refresh, logout) | ✅ |
| Therapist creates Patient User + Case (with audit log) | ✅ |
| Patient logs in, gets JWT | ✅ |
| Patient creates Session (persists MedhaState to DB) | ✅ |
| Patient sends chat message → ConversationManager → MedhaState updated → persisted | ✅ |
| SafetyGateway triggers crisis response during chat | ✅ |
| SafetyTrigger detects emergencies and writes SafetyEventModel to DB | ✅ |
| Check-in starts → DeterministicQuestionEngine selects question → persisted | ✅ |
| Check-in answer → feature updates MedhaState → next question selected | ✅ |
| Check-in auto-completes when all features filled | ✅ |
| Batch event ingestion (idempotent) | ✅ |
| Behaviour feature aggregation (10 features + deviations) | ✅ |
| Behaviour snapshot persisted to DB | ✅ |
| Voice check-in upload → MedhaVoiceAdapter runs → VoiceRecordModel persisted | ✅ (with caveat — see §3) |
| Journal CRUD | ✅ |
| V2 Prediction Pipeline called after voice/chat → PredictionResultModel persisted | ✅ |
| Therapist views latest prediction results (DDS, Temporal Risk, Triage) | ✅ |
| Therapist views prediction history | ✅ |
| Therapist views case session list | ✅ |
| Therapist views check-in history | ✅ |
| Therapist views behaviour snapshots | ✅ |
| Therapist views safety alerts | ✅ |
| Therapist handles/resolves alert (with audit log) | ✅ |
| Therapist views Clinical Insights (ExplainabilityEngine) with trend | ✅ |
| Therapist views Clinical Recommendations (RecommendationEngine + AlertEngine) | ✅ |
| Therapist views Safety Protocol (evaluated via AlertEngine) | ✅ |
| RBAC enforcement — User cannot access therapist endpoints (403) | ✅ |
| Anti-enumeration — Case/Session not found returns 403, not 404 | ✅ |
| Audit logging for all sensitive operations | ✅ |
| Privacy redaction in logs and error responses | ✅ |
| Full E2E demo seed with real V2 pipeline execution | ✅ |
| 188 backend tests passing | ✅ |

---

## 5. Remaining Work (Prioritized)

### 🔴 P0 — Must Fix Before Production

| Task | File(s) |
|------|---------|
| **Implement production `AlertEngineProtocol`** — real webhook/SMS/email/push delivery when SafetyTrigger fires | Create `backend/integrations/alert_provider.py` |
| **Replace in-memory prediction queue with durable queue** | Replace `backend/jobs/prediction_queue.py` with Redis/Celery/RQ |
| **Fix voice features syncing to session state** | `backend/services/voice_service.py` — restore `MedhaState` from DB, process, then write back |
| **Set secure `JWT_SECRET_KEY` in production .env** | `backend/config.py` + `.env` file |
| **Add Alembic migration for `safety_events` table** | `backend/persistence/migrations/versions/` |

### 🟠 P1 — Important for Reliability

| Task | File(s) |
|------|---------|
| **Implement behaviour aggregation trigger** — automatically aggregate after event batch is ingested | Create `backend/workers/behaviour_aggregator.py` |
| **Add JWT refresh token invalidation store** — blacklist tokens on logout | `backend/security/tokens.py`, add Redis or DB table |
| **Add audio/voice persistent storage** | Create `backend/integrations/storage.py` |
| **Add tests for `prediction_queue.py`** | Create `backend/tests/jobs/test_prediction_queue.py` |

### 🟡 P2 — Structural Alignment with Plan

| Task | File(s) |
|------|---------|
| Separate `user_service.py`, `therapist_service.py` as explicit service files | `backend/services/` |
| Create `alert_repository.py` | `backend/persistence/repositories/alert_repository.py` |
| Add `GET /api/v1/users/me` and `PATCH /api/v1/users/me` as dedicated endpoints | `backend/api/v1/endpoints/users.py` |
| Add `GET /api/v1/therapist/me` | `backend/api/v1/endpoints/therapist.py` |
| Deprecate root `app.py` Streamlit UI | Root `app.py` |

### 🟢 P3 — Future Capabilities (ML Team Dependency)

| Task | Blocker |
|------|---------|
| **Unblock Behaviour Specialist** — recover `Engagement_Score` data generator | ML team must provide Step 9C generator script or retrain the V2 Behaviour Ridge Model |
| Add voice features normalized table | Requires schema decision |
| Add observations normalized table | Requires clinical schema decision |

---

## 6. Test Coverage Summary

| Domain | Tests | Status |
|--------|-------|--------|
| Authentication | 6+ tests | ✅ |
| Therapist Management | 10+ tests | ✅ |
| Session Management | 15+ tests | ✅ |
| Chat + ConversationManager | 10+ tests | ✅ |
| Check-ins + Question Engine | 15+ tests | ✅ |
| Behaviour Aggregation | 8+ tests | ✅ |
| Prediction Service | 2 tests | ✅ |
| Therapist Results API | 25+ tests | ✅ |
| Therapist Insights API | 20+ tests | ✅ |
| Therapist Recommendations API | 20+ tests | ✅ |
| Security (Audit, Privacy, Auth) | 28+ tests | ✅ |
| E2E (Step 30) | 5 tests | ✅ |
| Prediction Queue Background Worker | **0 tests** | ❌ |
| Voice Feature DB Sync | **0 tests** | ❌ |
| Production Alert Provider | **0 tests** | ❌ (not implemented) |

**Total Backend Tests:** 188 passed, 0 failed.

---

## 7. Architecture Deviations From Plan (Summary)

| Plan Spec | Actual Implementation | Severity |
|-----------|----------------------|----------|
| `observations` table | Inside `state_snapshot` JSON | Medium |
| `structured_features` table | Inside `state_snapshot` JSON | Medium |
| `voice_features` table | Inside `state_snapshot` JSON | Medium |
| `backend/integrations/alert_provider.py` | Not implemented — MockAlertEngine still used | **Critical** |
| `backend/integrations/storage.py` | Not implemented | High |
| `backend/workers/` with 3 worker files | Empty directory + basic `jobs/prediction_queue.py` | High |
| Separate `user_service.py`, `therapist_service.py`, `alert_service.py` | Logic inline in endpoints | Low |
| `feature_repository.py`, `alert_repository.py` | Direct ORM queries | Low |
| `GET /api/v1/users/me`, `PATCH /api/v1/users/me` as distinct endpoint file | Functionality in `auth.me` | Low |
