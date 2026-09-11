# FINAL MEDHA BACKEND AUDIT REPORT

**Project**: MEDHA (Multimodal Emotion & Diagnostic Healthcare Assistant)  
**System**: MEDHA Backend Integration & Clinical Application Service  
**Date**: September 11, 2026  
**Auditor**: Antigravity Automated Verification Agent  
**Specification**: `backend/docs/backend_plan.md` §35  
**Final Status**: STEP 35 AUDIT COMPLETE (293/293 TESTS PASSING)  

---

## 1. Executive Summary

This document represents the authoritative, conclusive audit of the MEDHA Backend system, encompassing all 35 steps defined in `backend/docs/backend_plan.md`. 

The MEDHA Backend was engineered to connect the frontend applications (Patient Mobile/Web App and Therapist Clinical Dashboard) to the pre-existing, frozen core intelligence engines:
1. **The Frozen Conversational Engine**: Rule-based dialogue manager and safety escalation engine (`chatbot/core/conversation_manager.py`).
2. **The Deterministic Question Engine**: Dynamic clinical questionnaire router (`engine/question_engine/deterministic_question_engine.py`).
3. **The Frozen MEDHA V2 Fusion Pipeline**: Multimodal ensemble (`engine/v2/`) performing late fusion across text, speech, and journal modalities with dynamic missingness tolerance.

The backend does **not** duplicate machine learning models, does not invent new conversational trees, and does not alter frozen clinical weights. Its purpose has been executed under seven architectural mandates: **AUTHENTICATE**, **AUTHORIZE**, **PERSIST**, **ORCHESTRATE**, **INTEGRATE**, **PROTECT**, and **SERVE**.

### Audit Snapshot
- **Total Backend Steps Executed**: 35 / 35 (100%)
- **Test Suite Results**: 293 tests collected, **293 passed (100%)**, 0 failed, 0 errors.
- **Execution Time**: 429.81s (~7 minutes) under Python 3.13.1.
- **Security & Privacy Status**: Zero leaks of predictions or internal clinical scores to patient endpoints; therapist ownership isolation verified with anti-enumeration protection; constant-time token comparisons; PII-redacted audit logs; non-blocking asynchronous safety escalation.
- **Database Status**: Fully verified 5-revision Alembic migration chain supporting complete round-trip schema generation (`upgrade head` $\rightarrow$ `downgrade base` $\rightarrow$ `upgrade head`) and operating idempotently with SQLite (dev/test) and PostgreSQL (production).

---

## 2. Architecture Verification

The implementation follows the core architectural boundary rules established in `backend/docs/backend_plan.md` §22 and §24:

```
+-----------------------------------------------------------------------------------+
|                              Client Layer (Web / Mobile)                          |
+-----------------------------------------+-----------------------------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                  (Patient Token)                   (Therapist Token)
                        |                                   |
+-----------------------v-----------------------------------v-----------------------+
|                               MEDHA FastAPI Backend                               |
|                                                                                   |
|  [AUTHENTICATE]  JWT Bearer tokens, Argon2/Bcrypt password hashing                |
|  [AUTHORIZE]     Strict RBAC: USER vs THERAPIST, case assignment ownership        |
|  [PROTECT]       Input validation, PII redaction, non-blocking safety alerts      |
|  [ORCHESTRATE]   Session snapshots, multi-turn state, event telemetry aggregation |
|  [PERSIST]       SQLAlchemy ORM + Alembic (cases, sessions, answers, predictions)  |
|  [INTEGRATE]     Deterministic Question Engine, ConversationManager, V2 Pipeline  |
|  [SERVE]         REST API (Patient Chat/Check-in, Therapist Dashboard & Insights) |
+-----------------------+-----------------+-----------------+-----------------------+
                        |                 |                 |
                        v                 v                 v
             +--------------------+ +-----------+ +--------------------+
             |   Chatbot Core     | |  Question | |  Frozen MEDHA V2   |
             | ConversationManager| |  Engine   | | Late Fusion Models |
             +--------------------+ +-----------+ +--------------------+
```

### 1. AUTHENTICATE
- Implemented via `backend/security/auth.py` and endpoints in `backend/api/v1/endpoints/auth.py`.
- Employs cryptographically secure token generation (`python-jose`), standard bearer authorization headers, password hashing via `passlib[bcrypt]` / argon2, and token expiration handling with `/refresh` mechanics.
- Timing attack mitigations implemented via constant-time token comparison routines (`backend/security/utils.py`).

### 2. AUTHORIZE
- Role-Based Access Control (RBAC) enforced via FastAPI dependency injection (`backend/security/rbac.py`).
- Strict bifurcation of roles: `USER` (patients) and `THERAPIST` (clinicians).
- Ownership verification: Access to clinical records, longitudinal results, alerts, and predictions requires verified assignment (`case.therapist_id == current_therapist.id`). Foreign case inquiries result in uniform `HTTP 403 Forbidden` with anti-enumeration error masking.

### 3. PERSIST
- Relational schema managed via SQLAlchemy 2.0 ORM and tracked by 5 consecutive Alembic migrations (`backend/alembic/versions/`).
- Handles users, therapist profiles, clinical cases, persistent chat sessions, chat messages, check-in questionnaires, check-in answers, raw telemetry events, aggregate behavioural timepoints, and fused multi-specialist predictions.
- Schema round-trip, constraint consistency, foreign key cascades, and table reflection verified from clean databases exclusively via Alembic.

### 4. ORCHESTRATE
- Dialogue turns are orchestrated through `ChatbotService`, restoring conversational session state from database snapshots before invoking the chatbot core, and persisting updated state snapshots after each turn.
- Longitudinal check-in answers are accumulated as structured, non-diagnostic symptom monitoring signals and self-reported wellness indicators for clinician review.
- High-volume raw telemetry events are collected and transformed by `BehaviourAggregatorService` into hourly/daily summary timepoints.

### 5. INTEGRATE
- Clean adapter patterns encapsulate legacy components:
  - `ChatbotService` delegates to `chatbot.core.conversation_manager.ConversationManager`.
  - `CheckInService` delegates to `engine.question_engine.deterministic_question_engine.DeterministicQuestionEngine`.
  - `MedhaV2Adapter` interfaces with frozen `engine/v2/` late-fusion models, scalers, and imputers.
- Backend code introduces zero duplicate ML inference code or synthetic prompt generators.

### 6. PROTECT
- Zero leakage of raw diagnostic prediction vectors (`depression_probability`, `anxiety_probability`, `risk_level`, `trajectory`) to patient endpoints.
- Safety triggers in `SafetyService` detect high-risk signals (self-harm, crisis phrases) during patient chat turns and dispatch background alerts to assigned therapists without blocking or aborting the active dialogue turn.
- Structured audit logging (`backend/security/audit.py`) records all authentication and clinical record access events with strict PII scrubbing.

### 7. SERVE
- Fully typed, OpenAPI/Swagger documented endpoints under `/api/v1/`.
- Clear separation between patient routes (`/chat`, `/checkin`, `/events`, `/voice`, `/journal`) and clinician routes (`/therapist/cases`, `/results`, `/predictions`, `/insights`, `/recommendations`, `/alerts`).
- Deep operational readiness (`GET /api/v1/ready`) checking database connectivity, connection pool metrics, and ML artifact availability alongside shallow liveness (`GET /api/v1/health`).

---

## 3. Verification of 12 Authoritative Invariants

All 12 core architectural invariants mandated by `backend/docs/backend_plan.md` §35 have been thoroughly inspected and verified:

| # | Invariant Mandate | Verification Status | Implementation & Architectural Evidence |
|---|-------------------|---------------------|-----------------------------------------|
| **1** | **Existing chatbot remains authoritative** | **VERIFIED** | `ChatbotService.process_message()` wraps `ConversationManager.process_turn()` without altering intents, slot fillers, or crisis logic. Tested in `test_chatbot_integration.py` & `test_step12_integration.py`. |
| **2** | **Question Engine remains authoritative** | **VERIFIED** | `CheckInService.get_next_question()` and `submit_answer()` invoke `DeterministicQuestionEngine` directly. The question sequencing tree is completely untouched. Tested in `test_checkin_integration.py` & `test_step13_checkins.py`. |
| **3** | **V2 remains frozen** | **VERIFIED** | All `.pkl` model weights, scalers, imputers, and ridge fusion weights in `engine/v2/` are loaded read-only by `MedhaV2Adapter`. Hash and parameter stability confirmed in `test_v2_integration.py` & `test_step32_behaviour_v2_integration.py`. |
| **4** | **Backend never directly exposes specialist models** | **VERIFIED** | Raw specialist predictions (`text_pred`, `speech_pred`, `journal_pred`, `behav_pred`) are encapsulated within late fusion and therapist results layers. No direct specialist route exists. Tested in `test_privacy_hardening.py`. |
| **5** | **USER and THERAPIST roles are enforced** | **VERIFIED** | Strict role guards (`require_role(UserRole.THERAPIST)` and `require_role(UserRole.USER)`) reject invalid roles across all endpoints. Cross-role access returns `HTTP 403`. Tested in `test_auth_api.py` & `test_step31_security_integration.py`. |
| **6** | **Therapist ownership isolation works** | **VERIFIED** | `TherapistResultsService` enforces that the querying clinician owns `case.therapist_id`. Querying foreign cases returns `HTTP 403` with anti-enumeration protection. Tested in `test_authorization_audit.py` & `test_step31_security_integration.py`. |
| **7** | **Predictions are therapist-only** | **VERIFIED** | Prediction routes are mounted exclusively under `/api/v1/therapist/`. Patient chat response schemas (`schemas/chat.py`) contain zero clinical scores, prediction probabilities, or risk classifications. Tested in `test_privacy_hardening.py`. |
| **8** | **Missingness is preserved** | **VERIFIED** | Unobserved modalities are kept as explicit `None` / `NULL`. Never imputed as `0.0`. `MedhaV2Adapter` identifies available modality masks and delegates to the appropriate submodel. Tested in `test_step32_behaviour_v2_integration.py`. |
| **9** | **Behaviour events are idempotent** | **VERIFIED** | `EventRepository.batch_insert_idempotent()` deduplicates on `raw_events.event_id` via unique constraint and conflict suppression. Retransmissions cause 0 duplicate records. Tested in `test_event_ingestion.py` & `test_step32_behaviour_v2_integration.py`. |
| **10** | **Safety alerts are non-blocking** | **VERIFIED** | `SafetyService.dispatch_alert()` dispatches crisis alerts asynchronously in background tasks. Notification transport failure does not fail or delay the active chat turn. Tested in `test_chatbot_integration.py` & `test_step30_e2e_flow.py`. |
| **11** | **Sessions can be reconstructed** | **VERIFIED** | Dialogue state snapshots are serialized to JSON in `chat_sessions.state_snapshot`. `ChatbotService._restore_session_state()` accurately restores state across turns and restarts. Tested in `test_session_restoration.py`. |
| **12** | **Complete test suite passes** | **VERIFIED** | Pytest executes **293 tests collected with 100% passing (293 passed, 0 failures, 0 errors)** in 429.81 seconds. |

---

## 4. Completed Components / Steps 1–34

A chronological matrix of all backend development steps completed prior to this final audit:

| Steps | Component Area | Key Files & Artifacts | Status |
|-------|----------------|-----------------------|--------|
| **Step 1** | Repository & Architecture Audit | `backend/docs/AUDIT.md`, `backend/docs/backend_plan.md` | Completed & Verified |
| **Step 2** | FastAPI Application Foundation | `backend/main.py`, `backend/config.py`, `backend/tests/test_app.py` | Completed & Verified |
| **Step 3** | Database Persistence Infrastructure | `backend/database.py`, `backend/alembic/`, `backend/tests/test_database.py` | Completed & Verified |
| **Step 4** | User & Therapist ORM Models | `backend/models/user.py`, `backend/models/therapist.py`, `test_user_models.py` | Completed & Verified |
| **Step 5** | Authentication & JWT Issuance | `backend/security/auth.py`, `backend/tests/test_auth_api.py` | Completed & Verified |
| **Step 6** | Case & Session Management | `backend/services/case_service.py`, `backend/tests/test_case_service.py` | Completed & Verified |
| **Step 7** | Therapist Creates Users | `backend/api/v1/endpoints/therapist.py`, `backend/tests/test_therapist_api.py` | Completed & Verified |
| **Step 8** | Check-in Question Engine Integration | `backend/services/checkin_service.py`, `backend/tests/test_checkin_integration.py` | Completed & Verified |
| **Step 9A–C** | Behaviour Aggregation & V2 Lineage | `backend/services/behaviour_aggregator_service.py`, `docs/STEP_9A-C*.md` | Completed & Verified |
| **Step 10** | Persistent Chatbot Integration | `backend/services/chatbot_service.py`, `backend/tests/test_chatbot_integration.py` | Completed & Verified |
| **Step 11** | Therapist Results APIs | `backend/services/therapist_results_service.py`, `test_therapist_results_api.py` | Completed & Verified |
| **Step 12** | Chatbot Full Integration | `backend/api/v1/endpoints/chat.py`, `backend/tests/test_step12_integration.py` | Completed & Verified |
| **Step 13** | Check-in Persistence & History | `backend/api/v1/endpoints/checkin.py`, `backend/tests/test_step13_checkins.py` | Completed & Verified |
| **Step 14** | Structured Feature Extraction | `backend/services/feature_service.py`, feature extraction pipelines | Completed & Verified |
| **Step 15** | Idempotent Event Ingestion | `backend/repositories/event_repository.py`, `backend/tests/test_event_ingestion.py` | Completed & Verified |
| **Step 16** | Behaviour Aggregation Testing | `backend/tests/test_behaviour_aggregator.py` | Completed & Verified |
| **Step 17** | Voice Integration Endpoint | `backend/api/v1/endpoints/voice.py`, `backend/tests/api/test_voice_api.py` | Completed & Verified |
| **Step 18** | Journal Integration Endpoint | `backend/api/v1/endpoints/journal.py`, `backend/tests/api/test_journal_api.py` | Completed & Verified |
| **Step 19** | Frozen V2 Adapter | `backend/services/v2_adapter.py`, `backend/tests/integration/test_v2_integration.py` | Completed & Verified |
| **Step 20** | Asynchronous Prediction Service | `backend/services/prediction_service.py`, `test_prediction_service.py` | Completed & Verified |
| **Step 21** | Triage Logic & Classification | `backend/services/triage_service.py`, risk severity rules | Completed & Verified |
| **Step 22** | Therapist Prediction APIs | `backend/api/v1/endpoints/therapist.py`, prediction history endpoints | Completed & Verified |
| **Step 23** | Therapist Behaviour/Check-in APIs | `backend/api/v1/endpoints/therapist.py`, longitudinal check-in views | Completed & Verified |
| **Step 24** | Therapist Safety Alerts APIs | `backend/services/safety_service.py`, alert dispatch mechanisms | Completed & Verified |
| **Step 25** | Clinical Insights Engine | `backend/api/v1/endpoints/therapist.py`, `test_therapist_insights_api.py` | Completed & Verified |
| **Step 26** | Clinical Recommendations APIs | `backend/api/v1/endpoints/therapist.py`, `test_therapist_recommendations_api.py` | Completed & Verified |
| **Step 27** | Authorization Audit | `backend/tests/test_authorization_audit.py`, 12 authorization tests | Completed & Verified |
| **Step 28** | Privacy Audit & Hardening | `backend/tests/test_privacy_hardening.py`, PII redaction tests | Completed & Verified |
| **Step 29** | Audit Logging Verification | `backend/security/audit.py`, `backend/tests/test_step29_audit_verification.py` | Completed & Verified |
| **Step 30** | End-to-End User Flow & Seed | `backend/scripts/seed.py`, `backend/tests/test_step30_e2e_flow.py`, `test_step30_seed_verification.py` | Completed & Verified |
| **Step 31** | Security Integration Test Suite | `backend/tests/test_step31_security_integration.py` (70 tests) | Completed & Verified |
| **Step 32** | Behaviour / V2 Integration Tests | `backend/tests/test_step32_behaviour_v2_integration.py` (9 tests) | Completed & Verified |
| **Step 33** | Production Configuration Hardening | `backend/config.py`, `GET /api/v1/ready`, `test_step33_production_config.py` (19 tests) | Completed & Verified |
| **Step 34** | Database Migration Verification | `backend/tests/test_step34_migration_verification.py` (7 tests) | Completed & Verified |

---

## 5. Security & Privacy Findings

The security posture of the MEDHA backend has been hardened across authentication, authorization, data masking, anti-enumeration, and audit logging:

1. **Authentication Rigor**:
   - JWT tokens use HMAC-SHA256 signatures with validated secret strength.
   - Default developmental secret fallback is strictly rejected when `ENVIRONMENT=production`.
   - Token decoding enforces expiration timestamps (`exp`) and standard claims (`sub`, `role`).
   - Constant-time secret comparison prevents remote side-channel timing attacks.

2. **Therapist Ownership & Anti-Enumeration Isolation**:
   - Access to clinical data requires authenticated `THERAPIST` credentials.
   - When a therapist attempts to view, update, or inspect a case assigned to another clinician, the backend returns `HTTP 403 Forbidden` with a standardized, non-leaking error message (`"Access denied to this case"`).
   - The response does not reveal whether the unassigned case ID exists, preventing patient ID enumeration.

3. **Zero Prediction Leakage to Patient Applications**:
   - Patient-facing chat schemas (`schemas/chat.py`), check-in schemas (`schemas/checkin.py`), and event ingestion responses contain zero references to clinical probabilities, depression/anxiety scores, or risk levels.
   - Validation exception handlers intercept FastAPI/Pydantic validation errors and scrub raw patient inputs from error payloads.

4. **Non-Blocking Crisis Escalation**:
   - Patient statements with high safety triggers immediately invoke `SafetyService.dispatch_alert()` via FastAPI `BackgroundTasks`.
   - The user's active conversational turn receives an immediate, compassionate de-escalation response without waiting on network delivery of therapist alerts.
   - Crisis delivery failures are trapped, logged, and audited without disrupting patient dialogue.

5. **Audit Logging & PII Scrubbing**:
   - Sensitive security events (login successes/failures, unauthorized access attempts, clinical result views) are written to structured audit storage (`audit_logs` table).
   - Authorization headers, passwords, and raw conversational text are scrubbed prior to persistence.

---

## 6. Complete Test Suite Verification

The entire backend automated test suite was executed in an isolated audit pass:

```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\Kavita\Desktop\MEDHA
plugins: anyio-4.12.1, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False
collected 293 items

backend\tests\api\test_journal_api.py ..                                 [  0%]
backend\tests\api\test_voice_api.py .                                    [  1%]
backend\tests\integration\test_v2_integration.py .                       [  1%]
backend\tests\jobs\test_prediction_queue.py ..                           [  2%]
backend\tests\services\test_prediction_service.py .                      [  2%]
backend\tests\test_account_repositories.py ..                            [  3%]
backend\tests\test_app.py .......                                        [  5%]
backend\tests\test_audit_logging.py ..........                           [  8%]
backend\tests\test_auth_api.py .........                                 [ 11%]
backend\tests\test_authorization_audit.py ............                   [ 16%]
backend\tests\test_behaviour_aggregator.py .....                         [ 17%]
backend\tests\test_case_models.py ...                                    [ 18%]
backend\tests\test_case_service.py .                                     [ 19%]
backend\tests\test_chatbot_integration.py ..                             [ 19%]
backend\tests\test_checkin_integration.py ..                             [ 20%]
backend\tests\test_database.py ........                                  [ 23%]
backend\tests\test_event_ingestion.py ...                                [ 24%]
backend\tests\test_health.py ..                                          [ 24%]
backend\tests\test_migrations.py .                                       [ 25%]
backend\tests\test_privacy_hardening.py ......                           [ 27%]
backend\tests\test_security_utils.py ..                                  [ 27%]
backend\tests\test_session_repository.py .                               [ 28%]
backend\tests\test_session_restoration.py ..                             [ 29%]
backend\tests\test_sessions_api.py .........                             [ 32%]
backend\tests\test_step12_integration.py .............                   [ 36%]
backend\tests\test_step13_checkins.py .......                            [ 38%]
backend\tests\test_step29_audit_verification.py .....                    [ 40%]
backend\tests\test_step30_e2e_flow.py .                                  [ 40%]
backend\tests\test_step30_seed_verification.py ....                      [ 42%]
backend\tests\test_step31_security_integration.py ...................... [ 49%]
................................................                         [ 66%]
backend\tests\test_step32_behaviour_v2_integration.py .........          [ 69%]
backend\tests\test_step33_production_config.py ...................       [ 75%]
backend\tests\test_step34_migration_verification.py .......              [ 78%]
backend\tests\test_therapist_api.py .......                              [ 80%]
backend\tests\test_therapist_insights_api.py ..........                  [ 83%]
backend\tests\test_therapist_recommendations_api.py .........            [ 87%]
backend\tests\test_therapist_results_api.py ............................ [ 96%]
..                                                                       [ 97%]
backend\tests\test_user_models.py ........                               [100%]

================ 293 passed, 40 warnings in 429.81s (0:07:09) =================
```

### Key Metrics:
- **Total Tests Collected**: 293
- **Passed**: 293 (100.0%)
- **Failed**: 0
- **Errors**: 0
- **Execution Time**: 429.81s
- **Execution Environment**: Windows 11 / Python 3.13.1 / pytest 9.0.2

---

## 7. Known Limitations & Open Issues

In accordance with the MEDHA engineering charter, all architectural limits and lineage gaps are documented honestly:

### 1. Behaviour Specialist Blocked State (`behav_pred=None`, `behav_blocked=True`)
- **Root Cause**: During Step 9C, deep historical lineage tracing revealed that the synthetic feature generator script responsible for producing the legacy training label `Engagement_Score` was not preserved in the historical repository. 
- **Current Behavior**: Rather than synthesizing arbitrary, ungrounded weights or inventing a fake generator, the backend marks the Behaviour Specialist as explicitly blocked (`behav_pred=None`, `behav_blocked=True`).
- **Clinical & System Impact**: The frozen late-fusion engine (`MedhaV2Adapter`) was engineered with dynamic modality routing. When `behav_pred` is `None`, the fusion model dynamically selects the 3-specialist submodel (Text + Speech + Journal) without loss of mathematical stability or unhandled exceptions.

### 2. Auxiliary ORM Models outside Alembic Migration Chain
- **Scope**: `VoiceRecordModel`, `JournalEntryModel`, and `SafetyEventModel` exist in `backend/models/` and are registered with `Base.metadata`.
- **Migration Status**: The authoritative 5-migration Alembic chain creates the 11 primary clinical tables (`users`, `therapists`, `cases`, `chat_sessions`, `chat_messages`, `checkin_questionnaires`, `checkin_answers`, `raw_events`, `behaviour_timepoints`, `predictions`, `audit_logs`).
- **Operational Reality**: Step 34 proved that all core application workflows, authentication, check-ins, multi-turn chat, telemetry ingestion, and therapist dashboard queries run cleanly against a database initialized exclusively via Alembic without requiring the 3 auxiliary tables. If future steps require relational persistence of raw voice binary audio and journal text records, a dedicated migration should be scheduled.

### 3. Python 3.13 / Dependency Deprecation Warnings
- **Scikit-Learn Unpickling Warning**: V2 artifacts pickled under scikit-learn 1.9.0 produce non-fatal deprecation warnings when loaded under scikit-learn 1.8.0. Predictions execute normally.
- **SQLAlchemy Datetime Warning**: Calls using `datetime.datetime.utcnow()` generate deprecation notices in SQLAlchemy 2.0. These do not affect functionality and should be migrated to `datetime.datetime.now(datetime.timezone.utc)` during future maintenance.
- **Pydantic V2 ConfigDict**: Legacy `class Config` usage in `schemas/chat.py` generates notices recommending migration to `ConfigDict`.

---

## 8. Production Readiness & Recommendations

The MEDHA backend audit for Step 35 is complete, with all 293 automated tests passing. Deployment readiness is subject to the documented operational limitations and recommendations below:

1. **Environment Configuration**:
   - Set `ENVIRONMENT=production` in the deployment environment.
   - Set `SECRET_KEY` to a cryptographically random 256-bit base64 string. The application will abort startup if the default development key is detected in production.
   - Configure `ALLOWED_ORIGINS` to specific frontend domain origins; wildcards are strictly blocked in production.

2. **Database Provisioning**:
   - Run migrations before starting application workers:
     ```bash
     alembic upgrade head
     ```
   - Connect to managed PostgreSQL with connection pooling tuned via `DB_POOL_SIZE` (default: 10) and `DB_MAX_OVERFLOW` (default: 20).

3. **Server Execution**:
   - Execute using an ASGI production server (e.g., Uvicorn / Gunicorn with `UvicornWorker`):
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
     ```
   - Ensure external reverse proxies (e.g., NGINX, Cloudflare) route liveness checks to `GET /api/v1/health` and orchestrator readiness checks to `GET /api/v1/ready`.

---

## 9. Final Assessment

The MEDHA Backend Step 35 Audit is **COMPLETE**, with **293 of 293 automated tests passing (100%)**.

The backend satisfies the architectural and functional requirements of `backend/docs/backend_plan.md` without modifying frozen ML models, without duplicating clinical chatbot logic, and while strictly enforcing privacy and role isolation boundaries. Production deployment readiness remains subject to the documented operational limitations (specifically, the blocked Behaviour Specialist requiring dynamic 3-specialist fallback, the auxiliary ORM models outside the verified Alembic migration chain, and runtime environment hardening recommendations).

---
*Report completed by Antigravity Agent on 2026-09-11.*
