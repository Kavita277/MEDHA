# MEDHA Backend — Final Database Schema Specification
## Authoritative Database Contract for Step 4 Implementation

---

## 1. Executive Summary

This document establishes the definitive, authoritative PostgreSQL database schema and persistence contract for the MEDHA Backend. It resolves all architectural review findings, aligns strictly with the frozen MEDHA V2 predictive engine, preserves the integrity of `MedhaState` and `ConversationManager`, and provides the exact technical specification for Step 4 (SQLAlchemy Domain Models and Alembic Migrations).

### Core Architectural Guarantees:
1. **Zero Impact on Frozen V2 Engine:** The database schema wraps and serves the frozen MEDHA V2 machine learning pipeline (`MedhaV2Pipeline`, `MedhaV2Adapter`, feature dictionaries, XGBoost, Ridge, and PyTorch GRU models) without altering a single weight, feature name, threshold, or input convention.
2. **Missingness Preservation:** Rigid enforcement of the clinical principle that *missing data is not zero*. `NULL` explicitly denotes unobserved or missing values. Zero (`0.0`) is strictly preserved as an observed numeric measurement.
3. **Modality Availability Boundary:** Modality availability flags (`struct_available`, `text_available`, `voice_available`, `behav_available`) are persisted as PostgreSQL `BOOLEAN` primitives and mapped to the numeric `1.0`/`0.0` expected by the frozen V2 adapter at the application boundary.
4. **Longitudinal Timepoint Invariant:** Complete definition of the `Timepoint` lifecycle, tying sequential check-in and conversational epochs to the 7-step trailing history window required by the PyTorch GRU temporal risk model.
5. **Role-Based Clinical Firewalls:** Absolute separation between Patient (User) and Therapist access domains. Patients are strictly barred from accessing raw predictions, Fusion DDS scores, Temporal Risk metrics, triage tags, safety engine heuristics, or internal telemetry.
6. **Immutable Clinical & Audit History:** Critical safety events, alerts, predictions, and audit logs are append-only and protected against cascading deletes.
7. **Safe-by-Default Retention:** Data retention periods are defined by deployment/compliance policy, while database constraints enforce non-destructive referential integrity by default.

---

## 2. Architectural Boundaries

The MEDHA backend architecture is divided into discrete boundaries with explicit ownership:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT ACCESS BOUNDARY                                │
├─────────────────────────────────────────┬────────────────────────────────────────┤
│         PATIENT / USER DOMAIN           │            THERAPIST DOMAIN            │
│  - Active Chat Sessions & Messages      │  - Assigned Case Roster & Patient Bio  │
│  - Interactive Check-in Questionnaires  │  - Longitudinal DDS & Temporal Risk    │
│  - Self Journaling & Voice Check-ins    │  - Safety Triggers & Alert Resolution  │
│  - Personal Account Settings            │  - Structured & Behavioral Telemetry   │
└─────────────────────────────────────────┴────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION / SERVICE LAYER                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│  - Authentication & RBAC Middleware                                              │
│  - ConversationManager & MedhaState Lifecycle Coordinator                        │
│  - Question Engine (In-Memory Policy & Cooldown Selection)                       │
│  - FeatureMapper (Chat Observation -> Canonical Structured Feature)              │
│  - Safety Trigger & Alert Engine                                                 │
│  - MedhaV2Adapter (DB Feature Aggregation -> Longitudinal DataFrame -> V2)      │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER (POSTGRESQL)                           │
├──────────────────┬──────────────────┬──────────────────┬─────────────────────────┤
│  Identity & Case │   Chat & State   │ Check-in & Feats │ Predictions & Safety    │
│  - users         │ - chat_sessions  │ - checkin_sess   │ - predictions           │
│  - therapists    │ - chat_messages  │ - checkin_quests │ - prediction_history    │
│  - cases         │ - medha_state_   │ - checkin_answs  │ - safety_events         │
│  - case_assigns  │   snapshots      │ - struct_feats   │ - alerts                │
│                  │                  │ - behav_events   │ - audit_logs            │
│                  │                  │ - voice_metadata │                         │
│                  │                  │ - journal_entries│                         │
└──────────────────┴──────────────────┴──────────────────┴─────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         FROZEN MEDHA V2 ENGINE (READ-ONLY)                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│  - 42-Feature Structured XGBoost DDS Specialist                                  │
│  - 5-Feature MuRIL Text Ridge Specialist                                         │
│  - 5-Feature Acoustic Voice Ridge Specialist                                     │
│  - 10-Feature Telemetry Behaviour Ridge Specialist                               │
│  - Leakage-Free Fusion Final Model (`fusion_model.json`)                         │
│  - PyTorch Temporal GRU 7-Timestep Sequence Escalation Model (`best_gru_model`)  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Entity Relationship Overview

```text
       ┌──────────────┐                 ┌────────────────┐
       │    users     │                 │   therapists   │
       │ (Role: User) │                 │(Role:Therapist)│
       └──────┬───────┘                 └───────┬────────┘
              │ 1                               │ 1
              │                                 │
              │         ┌──────────────┐        │
              └────────►│    cases     │◄───────┘
                     1  │ (Victim_ID)  │  1
                        └──────┬───────┘
                               │ 
        ┌──────────────────────┼────────────────────────┬──────────────────────┐
        │ 1                    │ 1                      │ 1                    │ 1
        ▼                      ▼                        ▼                      ▼
┌───────────────┐      ┌───────────────┐        ┌───────────────┐      ┌───────────────┐
│ chat_sessions │      │checkin_session│        │struct_features│      │  predictions  │
└───┬───────┬───┘      └───────┬───────┘        └───────────────┘      └───────┬───────┘
    │ 1     │ 1                │ 1                                             │ 1
    ▼       ▼                  ▼                                               ▼
┌───────┐ ┌──────────┐ ┌───────────────┐                               ┌───────────────┐
│chat_  │ │medha_    │ │checkin_quest  │                               │prediction_    │
│message│ │state_    │ └───────┬───────┘                               │history        │
│       │ │snapshot  │         │ 1                                     └───────────────┘
└───────┘ └──────────┘         ▼
                       ┌───────────────┐
                       │checkin_answer │
                       └───────────────┘

Additional Case-Level Telemetry Feeds:
cases ──1:N──► behaviour_events (Append-only telemetry logs)
cases ──1:N──► voice_metadata   (Acoustic features & temporary S3 audio key)
cases ──1:N──► journal_entries  (Free-text diary & sentiment markers)
cases ──1:N──► safety_events    (NLP-detected acute clinical emergencies)
safety_events ──1:N──► alerts   (Therapist triage queue & escalation lifecycle)
```

---

## 4. Authentication / Identity Model

### Domain Concepts
- **`users`**: Central authentication table representing all human actors. Authentication credentials (bcrypt password hashes) and account lifecycle states (`is_active`, `deactivated_at`) reside here.
- **Roles**: Rigidly partitioned into `'user'` (patient), `'therapist'`, and `'admin'`.
- **`therapists`**: Specialized 1-to-1 extension table for users with role `'therapist'`, storing clinical registration, organization, and specialization metadata.

---

## 5. Case Model

### Domain Concepts & Invariants
- **Longitudinal Container**: A `case` is the primary longitudinal envelope grouping all interactions, check-ins, telemetry, and predictions for a patient.
- **`victim_id`**: The external immutable string identifier directly ingested by `MedhaV2Pipeline.predict_v2()`. It is guaranteed unique across all cases (`UNIQUE(victim_id)`).
- **Patient Mapping**: A patient (`users.id`) can have multiple historical cases across years, but at most **one active case** at any given moment. Enforced via a partial unique index: `UNIQUE(user_id) WHERE status = 'active'`.
- **Primary Therapist**: Every case has exactly one primary assigned therapist (`therapist_id UUID NOT NULL FK -> therapists.id`).
- **Reassignment & History**: Case transfers are supported. When a case is transferred, `cases.therapist_id` is updated, and an immutable record is inserted into `case_assignments` for clinical governance and accountability.
- **Closed Cases**: Cases marked `'closed'` are read-only clinical archives. They cannot receive new chat sessions, check-ins, or predictions unless formally reopened.

---

## 6. Chat Model

### Domain Concepts
- **`chat_sessions`**: Represents a bounded conversational dialogue session between the patient and the MEDHA assistant. Maps directly to `MedhaState.session_id`.
- **Session Lifecycle**: States include `'active'`, `'completed'`, and `'abandoned'`. A session is tied to the case's current longitudinal `timepoint`.
- **`chat_messages`**: Append-only sequence of user and assistant messages with UTC timestamps, roles (`'user'`, `'assistant'`, `'system'`), message content, and token/latency metadata.

---

## 7. MedhaState Persistence

### Architectural Realities & Guarantees
- **No Table-Level Reconstruction**: The database does **not** attempt to normalize `MedhaState` into dozens of relational tables. `MedhaState` contains intricate, dynamically evolving nested objects (`CandidateObservation`, `QuestionRecord`, `ConversationSummary`, `ContextEvent`, `PreviousPrediction`).
- **Native Serialization**: `MedhaState` already provides fully tested, loss-free `to_dict()`, `from_dict()`, `to_json()`, and `from_json()` methods.
- **Snapshot Capture Policy**:
  - **Turn-Level Checkpoints**: After each successful assistant response generation, a checkpoint snapshot is persisted into `medha_state_snapshots` within the active transaction. This guarantees zero data loss if a server crashes mid-session.
  - **Session-Close Final Snapshot**: When a session is concluded, a final snapshot is committed.
- **State Restoration**: To restore the chatbot session:
  ```sql
  SELECT state_payload 
  FROM medha_state_snapshots 
  WHERE chat_session_id = :session_id 
  ORDER BY created_at DESC 
  LIMIT 1;
  ```
  The retrieved JSON is passed directly into `MedhaState.from_dict(payload)`.
- **Storage Lifecycle & Defensive Foreign Key Semantics (Fix #6)**:
  - Chat sessions themselves are retained under organizational compliance policy.
  - Intermediate turn snapshots may be pruned by an application maintenance process (e.g., routine background worker after 30 days), retaining the final session snapshot.
  - The foreign key constraint `chat_session_id ON DELETE CASCADE` on `medha_state_snapshots` exists strictly as defensive referential behavior if a chat session is ever legitimately removed through controlled administrative cleanup or test teardown. It does not imply normal clinical data deletion.

---

## 8. Check-in Model

### Domain Concepts & Authoritative Lifecycle (Fix #1)
- **`checkin_sessions`**: Orchestrates a formal clinical questionnaire assessment. A check-in is linked to a `case_id` and the current sequential `timepoint`.
- **Authoritative Status Model**:
  ```text
  pending ──► in_progress ──► completed (Terminal success)
                         └──► missed    (Terminal expiry / uncompleted window)
  ```
  - **`pending`**: Check-in session scheduled for the current timepoint assessment window.
  - **`in_progress`**: Patient has initiated the questionnaire and begun answering questions.
  - **`completed`**: Patient has answered all presented questions and submitted the assessment.
  - **`missed`**: Assessment window expired or closed without completion. This terminal non-completion state directly feeds the canonical V2 behavioural telemetry metric `Missed_Checkin`.
- **`checkin_questions`**: Individual questions presented to the patient during the check-in, holding `question_id` (e.g., `'SF-01'`), the rendered prompt text, and cooldown deadlines.
- **`checkin_answers`**: User-submitted answers capturing both verbatim response text (`response_text`) and the extracted categorical or numeric token (`semantic_value`).

---

## 9. Question Engine Boundary

### Authoritative Responsibilities
- **In-Memory Selection Authority**: The `QuestionEngine` (located in `engine/QuestionEngine/`) remains the sole authority on question prioritization, adaptive selection, and cooldown evaluation based on `QuestionRecord` history.
- **Persistence Boundary**: The `CheckinService` queries prior answered questions from `checkin_questions` and `checkin_answers`, constructs the candidate pool, invokes the Question Engine in-memory, and writes the selected questions and answers to PostgreSQL.
- **Separation**: The database schema does not duplicate question selection logic or heuristics. It strictly records the *outputs* and *responses*.

---

## 10. Structured Feature Model

### Canonical Feature Storage & Semantics
- **`structured_features`**: Stores point-in-time canonical structured features required by the 42-feature Structured DDS specialist (`v2_structured_dds_features.json`).
- **Identity & Uniqueness**: Exactly one canonical value per feature per case per timepoint:
  ```sql
  UNIQUE(case_id, timepoint, feature_name)
  ```
- **Provenance & Source**: The `source` column tracks how the value was determined (e.g., `'feature_mapper'`, `'checkin'`, `'therapist_override'`, `'baseline_intake'`).
- **Value Semantics (Fix #5)**:
  - **MISSING**: `numeric_value IS NULL AND categorical_value IS NULL`.
  - **NUMERIC ZERO**: `numeric_value = 0.0 AND categorical_value IS NULL`.
  - **NON-ZERO NUMERIC**: `numeric_value = <val> AND categorical_value IS NULL`.
  - **CATEGORICAL**: `numeric_value IS NULL AND categorical_value = '<cat>'`.
  - **Constraint**: A database CHECK constraint prevents simultaneous non-null numeric and categorical values:
    ```sql
    CHECK (NOT (numeric_value IS NOT NULL AND categorical_value IS NOT NULL))
    ```

---

## 11. Behaviour Event Model

### Domain Concepts
- **`behaviour_events`**: Append-only telemetry log capturing user interaction events (e.g., `'app_open'`, `'chat_message_sent'`, `'checkin_completed'`, `'rapid_scroll'`, `'session_duration'`).
- **Idempotency**: Every event carries a client- or gateway-generated `event_id` with a database uniqueness constraint `UNIQUE(event_id)` to prevent duplicate ingestion upon mobile network retries.
- **Aggregation Boundary**: Raw events are aggregated over timepoint windows into the 10 canonical behavioural metrics (`v2_behaviour_dds_features.json`) by the Behaviour Service before feeding the V2 adapter.

---

## 12. Voice Model

### Domain Concepts & Privacy Guarantees
- **`voice_metadata`**: Stores acoustic signal metadata and feature outputs extracted by the acoustic pipeline (`Voice_Distress`, `Pause_Ratio`, `Pitch_Variance`, etc.).
- **Temporary Raw Audio (Fix #11)**:
  - Raw audio recordings (`.wav` files) are sensitive biometric data.
  - `s3_reference` is **NULLABLE**. It points to a temporary S3 staging object key (e.g., `s3://medha-audio-staging/cases/{case_id}/{session_id}/{uuid}.wav`).
  - **Lifecycle**: Raw audio has a strict 24-hour retention window governed by an S3 bucket lifecycle policy. Once acoustic features are extracted and persisted to `voice_metadata.features_extracted`, the raw audio is purged according to deployment storage policy, and `s3_reference` is cleared or marked expired.
  - **Failure Handling**: If acoustic feature extraction fails, `processing_status` is set to `'failed'`, `voice_available` is set to `FALSE`, and temporary audio is retained for up to 72 hours solely for diagnostic inspection before automated deletion.

---

## 13. Journal Model

### Domain Concepts
- **`journal_entries`**: Free-text therapeutic diary entries submitted by the user.
- **Fields**: Captures `title`, `content`, client timestamp, and optional automated NLP `sentiment_metadata` (e.g., polarity, distress indicators).
- **Access Boundary**: Visible to the author patient and their assigned primary therapist. Never exposed to unassigned therapists or external endpoints.

---

## 14. V2 Timepoint Model

### FINAL TIMEPOINT CONTRACT

The semantic meaning, lifecycle, and operational rules of `Timepoint` for the MEDHA system are finalized as follows:

```text
Timepoint Lifecycle Flow:
─────────────────────────────────────────────────────────────────────────────
[Timepoint N in Progress]
  ├── Patient engages in multi-turn chat sessions (chat_sessions.timepoint = N)
  ├── Behavioral telemetry logged (behaviour_events tagged / windowed)
  ├── Voice / Journal entries submitted
  └── Formal Check-in initiated (checkin_sessions.timepoint = N)
                                │
                                ▼
[Timepoint N Finalization Trigger]
  ├── Mechanism A: Completion of Canonical Check-in (checkin_sessions.status = 'completed')
  │       OR
  └── Mechanism B: Authorized Epoch Close (scheduled window expires, checkin missed/omitted)
                                │
                                ▼
[Timepoint N Prediction & Seal]
  ├── 1. Feature Mapper seals canonical 42 structured features for Timepoint N
  ├── 2. Behaviour aggregator calculates 10 behavioral metrics for Timepoint N (including Missed_Checkin)
  ├── 3. Text & Voice extractors seal distress features for Timepoint N
  ├── 4. MedhaV2Adapter loads historical sequence [1 .. N] for Victim_ID
  ├── 5. MedhaV2Pipeline.predict_v2() executes (Fusion DDS + PyTorch GRU)
  ├── 6. Canonical Prediction row committed: (case_id, timepoint = N)
  └── 7. Case advances: case.current_timepoint = N + 1
─────────────────────────────────────────────────────────────────────────────
```

#### Verified GRU Window Semantics (Fix #3):
> **EXACT REPOSITORY INVARIANT (`engine/v2/medha_v2_pipeline.py`):**  
> At timepoint $N$, the PyTorch GRU receives a 7-timestep sequential tensor comprising the **7 strictly prior consecutive timepoints $[N-7, N-6, N-5, N-4, N-3, N-2, N-1]$** to predict the temporal risk score and future escalation flag for timepoint $N$.  
> - The target observation at timepoint $N$ itself is **not** part of the input sequence tensor `[i-7 : i]`; it is the observation being evaluated.  
> - Therefore, temporal prediction is available **only when at least 7 preceding timepoints exist in the longitudinal sequence** (i.e., $N \ge 8$ in a 1-indexed sequential series).  
> - For $N \le 7$, `Temporal_Available` is `FALSE` (`0`), `Temporal_Risk_Score` is `NULL` (`NaN`), and `Future_Escalation_Flag` is `NULL` (`NaN`). Current Fusion DDS prediction is entirely unaffected and continues to function normally.

#### The 9 Unambiguous Timepoint Implementation Rules:
1. **What creates a new timepoint?**
   A new timepoint is created when a case is initialized (`timepoint = 1`) and advances to `N + 1` whenever the assessment epoch for timepoint `N` is finalized.
2. **When is a timepoint considered complete? (Fix #2)**
   A timepoint can be finalized by either:
   - **Mechanism A:** Completion of the canonical scheduled check-in (`checkin_sessions.status = 'completed'`), **OR**
   - **Mechanism B:** An authorized explicit or scheduled assessment-epoch close when no completed check-in exists (e.g., patient missed the check-in window, setting `status = 'missed'`, or an authorized administrative/therapist epoch close finalizes the monitoring interval).  
   *A completed check-in is normally the canonical assessment, but is NOT mandatory when an authorized epoch-close mechanism finalizes the timepoint.*
3. **Can multiple chat sessions belong to one timepoint?**
   **YES.** A patient may chat multiple times within a single monitoring epoch (e.g., morning and evening conversations within a weekly timepoint). All sessions during that epoch inherit `timepoint = N`.
4. **Can multiple check-ins belong to one timepoint?**
   **NO.** Exactly one canonical *completed* check-in session represents the primary assessment for a timepoint. This is enforced by `UNIQUE(case_id, timepoint) WHERE status = 'completed'`. When Mechanism B finalizes the timepoint without a completed check-in, zero completed check-in rows exist, fully satisfying the partial index.
5. **How do voice/text/behaviour/structured features align to it?**
   All observations, messages, and telemetry occurring while the case is at `timepoint = N` are aggregated into the canonical feature representation for `(case_id, timepoint = N)`.
6. **When is prediction generated?**
   The V2 prediction is generated immediately upon timepoint finalization (via Mechanism A or B). The adapter gathers the cumulative longitudinal dataset `[1 .. N]` for the `victim_id` so that the PyTorch GRU receives its full trailing sequence (`[i-7 : i]`).
7. **Can a timepoint be reprocessed?**
   **YES.** Reprocessing is supported through a controlled administrative/clinical service (e.g., upon bug fix or updated late data). Reprocessing archives the complete existing prediction row into `prediction_history` and updates the canonical row in `predictions` with an incremented `reprocessing_version` and refreshed provenance timestamps.
8. **Can historical timepoints be inserted out-of-order?**
   **NO.** Timepoints are strictly monotonic positive integers (`1, 2, 3, ...`). Out-of-order retro-insertion into past timepoints is strictly forbidden because the GRU sequence windowing relies on causal chronological ordering.
9. **What is the exact uniqueness rule?**
   - In `predictions`: `UNIQUE(case_id, timepoint)` represents the single active canonical prediction.
   - In `structured_features`: `UNIQUE(case_id, timepoint, feature_name)`.
   - In `checkin_sessions`: `UNIQUE(case_id, timepoint) WHERE status = 'completed'`.

---

## 15. Prediction Model

### Domain Concepts & Provenance (Fix #3 & Fix #9)
- **`predictions`**: Stores the canonical output of the frozen MEDHA V2 pipeline for each `(case_id, timepoint)`.
- **Frozen V2 Outputs Preserved**:
  - `fusion_dds`: `DOUBLE PRECISION` (0.0 to 100.0) — Fusion DDS prediction.
  - `temporal_risk`: `DOUBLE PRECISION` (0.0 to 1.0) — PyTorch GRU probability (or `NULL` if history < 7).
  - `temporal_available`: `BOOLEAN` — `TRUE` if GRU trailing window >= 7 was present.
  - `future_escalation_flag`: `INTEGER` — `1` (Escalation), `0` (Safe), or `NULL`.
  - `priority_level`: `VARCHAR(50)` — Clinical triage band (`'CRITICAL'`, `'HIGH'`, `'MEDIUM'`, `'LOW'`, `'UNKNOWN'`).
  - Specialist baseline predictions: `struct_pred`, `text_pred`, `voice_pred`, `behav_pred`.
- **Modality Availability Flags**:
  - `struct_available`: `BOOLEAN NOT NULL` (hardcoded True in V2).
  - `text_available`: `BOOLEAN NOT NULL` (True if text features present).
  - `voice_available`: `BOOLEAN NOT NULL` (True if voice features present).
  - `behav_available`: `BOOLEAN NOT NULL` (hardcoded True in V2).
- **Explicit Provenance Fields (Fix #3)**:
  - `pipeline_version`: `VARCHAR(50) NOT NULL` (e.g., `'v2.0.0-frozen'`).
  - `model_version`: `VARCHAR(50) NOT NULL` (e.g., `'xgb_ridge_gru_final'`).
  - `feature_set_version`: `VARCHAR(50) NOT NULL` (e.g., `'canonical_42_5_5_10'`).
  - `run_id`: `UUID NOT NULL` (unique inference identifier).
  - `reprocessing_version`: `INTEGER NOT NULL DEFAULT 1`.
  - `computed_at`: `TIMESTAMP WITH TIME ZONE NOT NULL`.
- **`prediction_history` (Fix #4)**: Complete audit table storing the full prior prediction snapshot before it was overwritten/updated by reprocessing.

---

## 16. Safety Event Model

### Domain Concepts
- **`safety_events`**: Immutable clinical record generated whenever the `SafetyTrigger` detects acute risk in user text (e.g., `'immediate_danger'`, `'self_harm_intent'`, `'suicidal_intent'`, `'threat_to_other'`, `'immediate_protection_concern'`).
- **Evidence Containment (Fix #12)**: Contains only the specific triggering text snippet (`evidence`), the detection `confidence`, the `trigger_type`, and the associated `chat_session_id`. Full historical chat logs and authentication tokens are strictly barred from this table.

---

## 17. Alert Model

### 1-to-Many Safety Event to Alert Relationship (Fix #10)
- **Review Finding Resolution**: In real-world clinical operations, an acute safety event can necessitate multiple alerts over time (e.g., initial alert to primary therapist, secondary escalation alert to an on-call clinical director if unacknowledged after 15 minutes, or alert reassignment).
- **Cardinality**: `SafetyEvent 1 ──< Alerts` (One safety event can spawn one or more alerts).
- **Uniqueness Removal**: `safety_event_id` is a foreign key with an index, **not** a unique constraint.
- **Alert Lifecycle**: `status` progresses through `'new'` -> `'acknowledged'` -> `'escalated'` -> `'resolved'`.
- **Resolution Tracking**: Captures `therapist_id`, `resolved_at`, and mandatory `resolution_notes`.

---

## 18. Audit Log Model

### Privacy & Governance (Fix #12)
- **`audit_logs`**: Append-only compliance log recording all sensitive system operations (e.g., therapist reviewing patient chart, viewing predictions, exporting records, resolving alerts).
- **Strict Privacy Firewalls**:
  - **FORBIDDEN IN AUDIT LOGS**: Passwords, bcrypt hashes, JWT tokens, API keys, session secrets, full conversation transcripts, unencrypted clinical notes.
  - **PERMITTED IN AUDIT LOGS**: Actor UUID, actor role, action enum (`VIEW_CASE`, `ACK_ALERT`, `RESOLVE_ALERT`, `REPROCESS_TIMEPOINT`), target resource type, target resource ID, client IP address, user agent, execution status, and sanitized operational metadata.

---

## 19. Complete Table Specifications

### 19.1. `users`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Unique user identifier |
| `email` | `VARCHAR(255)` | NO | UNIQUE | Login email address |
| `password_hash` | `VARCHAR(255)` | NO | None | Bcrypt password hash |
| `role` | `VARCHAR(32)` | NO | `'user'`, CHECK in (`'user'`, `'therapist'`, `'admin'`) | System role |
| `is_active` | `BOOLEAN` | NO | `TRUE` | Account status flag |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Last profile update timestamp |
| `deactivated_at` | `TIMESTAMPTZ` | YES | `NULL` | Soft deletion timestamp |

### 19.2. `therapists`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | PK, FK -> `users.id` ON DELETE RESTRICT | Therapist profile ID |
| `license_number`| `VARCHAR(100)` | NO | UNIQUE | Professional clinical license |
| `specialization`| `VARCHAR(255)` | YES | `NULL` | Clinical domain focus |
| `organization`  | `VARCHAR(255)` | YES | `NULL` | Affiliated clinic or hospital |
| `created_at`    | `TIMESTAMPTZ`  | NO | `CURRENT_TIMESTAMP` | Profile creation timestamp |
| `updated_at`    | `TIMESTAMPTZ`  | NO | `CURRENT_TIMESTAMP` | Profile update timestamp |

### 19.3. `cases`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Primary case identifier |
| `victim_id` | `VARCHAR(100)` | NO | UNIQUE | External V2 pipeline string ID |
| `user_id` | `UUID` | NO | FK -> `users.id` ON DELETE RESTRICT | Assigned patient |
| `therapist_id` | `UUID` | NO | FK -> `therapists.id` ON DELETE RESTRICT | Primary assigned clinician |
| `current_timepoint`| `INTEGER` | NO | `1`, CHECK (`>= 1`) | Active longitudinal timepoint |
| `status` | `VARCHAR(32)` | NO | `'active'`, CHECK in (`'active'`, `'closed'`, `'on_hold'`) | Case lifecycle status |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Case opening timestamp |
| `updated_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Last case update timestamp |
| `closed_at` | `TIMESTAMPTZ` | YES | `NULL` | Case closure timestamp |

*Constraints:* Partial index `UNIQUE(user_id) WHERE status = 'active'` ensures at most one active case per user.

### 19.4. `case_assignments`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Assignment record ID |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `therapist_id` | `UUID` | NO | FK -> `therapists.id` ON DELETE RESTRICT | Assigned clinician |
| `assigned_by` | `UUID` | NO | FK -> `users.id` ON DELETE RESTRICT | Authorizing user/admin |
| `reason` | `VARCHAR(255)` | YES | `NULL` | Reassignment rationale |
| `assigned_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Assignment timestamp |

### 19.5. `chat_sessions`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Chat session identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Parent case |
| `session_identifier`| `VARCHAR(100)` | NO | UNIQUE | String ID for `MedhaState.session_id` |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Longitudinal timepoint during session |
| `status` | `VARCHAR(32)` | NO | `'active'`, CHECK in (`'active'`, `'completed'`, `'abandoned'`) | Session lifecycle status |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Session start timestamp |
| `updated_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Last turn activity timestamp |
| `closed_at` | `TIMESTAMPTZ` | YES | `NULL` | Session conclusion timestamp |

### 19.6. `chat_messages`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Message identifier |
| `chat_session_id` | `UUID` | NO | FK -> `chat_sessions.id` ON DELETE RESTRICT | Parent session |
| `role` | `VARCHAR(32)` | NO | CHECK in (`'user'`, `'assistant'`, `'system'`) | Message sender |
| `content` | `TEXT` | NO | None | Message textual body |
| `metadata_payload`| `JSONB` | YES | `NULL` | Token counts, latency, safety flags |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Chronological send timestamp |

### 19.7. `medha_state_snapshots`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Snapshot record identifier |
| `chat_session_id` | `UUID` | NO | FK -> `chat_sessions.id` ON DELETE CASCADE | Parent chat session (defensive cascade) |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Parent case |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Session timepoint |
| `turn_index` | `INTEGER` | NO | CHECK (`>= 0`) | Sequential conversational turn number |
| `state_payload` | `JSONB` | NO | None | Native `MedhaState.to_dict()` JSON |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Checkpoint creation timestamp |

### 19.8. `checkin_sessions`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Check-in assessment identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Parent case |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Assessment timepoint |
| `status` | `VARCHAR(32)` | NO | `'pending'`, CHECK in (`'pending'`, `'in_progress'`, `'completed'`, `'missed'`) | Assessment lifecycle status |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Initiation timestamp |
| `completed_at` | `TIMESTAMPTZ` | YES | `NULL` | Completion timestamp |

*Constraints:* Partial index `UNIQUE(case_id, timepoint) WHERE status = 'completed'` ensures at most one canonical completed check-in per timepoint.

### 19.9. `checkin_questions`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Question instance identifier |
| `checkin_session_id` | `UUID` | NO | FK -> `checkin_sessions.id` ON DELETE CASCADE | Parent check-in |
| `question_id` | `VARCHAR(50)` | NO | None | Engine ID (e.g., `'SF-01'`) |
| `question_text` | `TEXT` | NO | None | Actual prompt rendered to user |
| `intent` | `VARCHAR(100)` | NO | None | Clinical target category |
| `asked_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Render timestamp |
| `cooldown_until` | `TIMESTAMPTZ` | YES | `NULL` | Engine cooldown window |

### 19.10. `checkin_answers`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Answer record identifier |
| `checkin_question_id`| `UUID` | NO | UNIQUE, FK -> `checkin_questions.id` ON DELETE CASCADE | Target question |
| `response_text` | `TEXT` | NO | None | Verbatim user response |
| `semantic_value`| `VARCHAR(100)` | YES | `NULL` | Extracted categorical / numeric token |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Submission timestamp |

### 19.11. `structured_features`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Feature record identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Assessment timepoint |
| `feature_name` | `VARCHAR(100)` | NO | None | Canonical name (e.g. `'Sleep'`) |
| `numeric_value` | `DOUBLE PRECISION`| YES | `NULL` | Continuous/numeric feature value |
| `categorical_value`| `VARCHAR(255)` | YES | `NULL` | Categorical feature value |
| `source` | `VARCHAR(100)` | NO | None | Source (e.g. `'feature_mapper'`) |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Materialization timestamp |

*Constraints:* 
- `UNIQUE(case_id, timepoint, feature_name)`
- `CHECK (NOT (numeric_value IS NOT NULL AND categorical_value IS NOT NULL))`

### 19.12. `behaviour_events`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Event record identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `event_type` | `VARCHAR(100)` | NO | None | Event name (e.g. `'app_open'`) |
| `payload` | `JSONB` | NO | `'{}'::jsonb` | Telemetry event properties |
| `event_id` | `VARCHAR(100)` | NO | UNIQUE | Client idempotency UUID |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Event occurrence timestamp |

### 19.13. `voice_metadata`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Voice session identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `session_id` | `VARCHAR(100)` | NO | None | Associated chat/check-in session |
| `duration_seconds`| `DOUBLE PRECISION`| NO | CHECK (`>= 0.0`) | Audio duration |
| `s3_reference` | `VARCHAR(512)` | YES | `NULL` | Staging S3 key (cleared after 24h) |
| `processing_status`| `VARCHAR(32)` | NO | `'pending'`, CHECK in (`'pending'`, `'processed'`, `'failed'`) | Processing status |
| `features_extracted`| `JSONB` | YES | `NULL` | Extracted acoustic metrics dictionary |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Recording timestamp |

### 19.14. `journal_entries`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Journal entry identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `title` | `VARCHAR(255)` | YES | `NULL` | Entry headline |
| `content` | `TEXT` | NO | None | Diary narrative body |
| `sentiment_metadata`| `JSONB` | YES | `NULL` | NLP sentiment markers |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | User submission timestamp |

### 19.15. `predictions`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Prediction record identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Assessment timepoint |
| `fusion_dds` | `DOUBLE PRECISION`| NO | CHECK (`>= 0.0 AND <= 100.0`)| V2 Fusion DDS score |
| `temporal_risk` | `DOUBLE PRECISION`| YES | `NULL`, CHECK (`>= 0.0 AND <= 1.0`)| PyTorch GRU score (or NULL) |
| `temporal_available`| `BOOLEAN` | NO | None | True if GRU history >= 7 |
| `future_escalation_flag`| `INTEGER` | YES | `NULL`, CHECK in (`0`, `1`)| High-risk threshold indicator |
| `priority_level`| `VARCHAR(50)` | YES | `NULL`, CHECK in (`'CRITICAL'`, `'HIGH'`, `'MEDIUM'`, `'LOW'`, `'UNKNOWN'`) | Clinical triage band |
| `priority_rationale`| `TEXT` | YES | `NULL` | Rule explanation for triage band |
| `struct_pred` | `DOUBLE PRECISION`| NO | None | Structured specialist DDS |
| `text_pred` | `DOUBLE PRECISION`| YES | `NULL` | Text specialist DDS (or NULL) |
| `voice_pred` | `DOUBLE PRECISION`| YES | `NULL` | Voice specialist DDS (or NULL) |
| `behav_pred` | `DOUBLE PRECISION`| NO | None | Behaviour specialist DDS |
| `struct_available`| `BOOLEAN` | NO | `TRUE` | True (mapped to 1.0 for V2) |
| `text_available` | `BOOLEAN` | NO | None | True/False (mapped to 1.0/0.0) |
| `voice_available`| `BOOLEAN` | NO | None | True/False (mapped to 1.0/0.0) |
| `behav_available`| `BOOLEAN` | NO | `TRUE` | True (mapped to 1.0 for V2) |
| `pipeline_version`| `VARCHAR(50)`| NO | None | e.g. `'v2.0.0-frozen'` |
| `model_version` | `VARCHAR(50)` | NO | None | e.g. `'v2_frozen_xgb_ridge_gru'` |
| `feature_set_version`|`VARCHAR(50)`| NO | None | e.g. `'canonical_42_5_5_10'` |
| `run_id` | `UUID` | NO | None | Unique inference run UUID |
| `reprocessing_version`|`INTEGER` | NO | `1`, CHECK (`>= 1`) | Incremented on recalculation |
| `inference_metadata`| `JSONB` | YES | `NULL` | Model inputs hash, timing stats |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Prediction generation timestamp |

*Constraints:* `UNIQUE(case_id, timepoint)`

### 19.16. `prediction_history` (Complete Snapshot — Fix #4)
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | History archive identifier |
| `prediction_id`| `UUID` | NO | FK -> `predictions.id` ON DELETE RESTRICT | Canonical prediction reference |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `timepoint` | `INTEGER` | NO | CHECK (`>= 1`) | Assessment timepoint |
| `fusion_dds` | `DOUBLE PRECISION`| NO | CHECK (`>= 0.0 AND <= 100.0`)| Archived Fusion DDS score |
| `temporal_risk` | `DOUBLE PRECISION`| YES | `NULL`, CHECK (`>= 0.0 AND <= 1.0`)| Archived PyTorch GRU score |
| `temporal_available`| `BOOLEAN` | NO | None | Archived GRU availability |
| `future_escalation_flag`| `INTEGER` | YES | `NULL`, CHECK in (`0`, `1`)| Archived escalation flag |
| `priority_level`| `VARCHAR(50)` | YES | `NULL` | Archived triage band |
| `priority_rationale`| `TEXT` | YES | `NULL` | Archived triage rationale |
| `struct_pred` | `DOUBLE PRECISION`| NO | None | Archived Structured specialist DDS |
| `text_pred` | `DOUBLE PRECISION`| YES | `NULL` | Archived Text specialist DDS |
| `voice_pred` | `DOUBLE PRECISION`| YES | `NULL` | Archived Voice specialist DDS |
| `behav_pred` | `DOUBLE PRECISION`| NO | None | Archived Behaviour specialist DDS |
| `struct_available`| `BOOLEAN` | NO | None | Archived Structured availability |
| `text_available` | `BOOLEAN` | NO | None | Archived Text availability |
| `voice_available`| `BOOLEAN` | NO | None | Archived Voice availability |
| `behav_available`| `BOOLEAN` | NO | None | Archived Behaviour availability |
| `pipeline_version`| `VARCHAR(50)`| NO | None | Pipeline version at inference time |
| `model_version` | `VARCHAR(50)` | NO | None | Model version at inference time |
| `feature_set_version`|`VARCHAR(50)`| NO | None | Feature set version |
| `run_id` | `UUID` | NO | None | Original inference run UUID |
| `reprocessing_version`|`INTEGER` | NO | None | Version number before update |
| `inference_metadata`| `JSONB` | YES | `NULL` | Original inference metadata |
| `original_created_at`|`TIMESTAMPTZ`| NO | None | Original prediction generation timestamp |
| `archived_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Archive timestamp |
| `archived_by` | `UUID` | YES | FK -> `users.id` ON DELETE SET NULL | Authorizing clinician/admin (NULL if system) |
| `archive_reason`| `VARCHAR(255)`| YES | `NULL` | Rationale for reprocessing |

### 19.17. `safety_events`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Safety event identifier |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `chat_session_id`| `UUID` | NO | FK -> `chat_sessions.id` ON DELETE RESTRICT | Chat session where detected |
| `trigger_type` | `VARCHAR(100)` | NO | None | e.g. `'immediate_danger'` |
| `evidence` | `TEXT` | NO | None | Specific trigger excerpt |
| `confidence` | `DOUBLE PRECISION`| YES | `NULL` | Classifier score (0.0 to 1.0) |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Detection timestamp |

### 19.18. `alerts`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Alert record identifier |
| `safety_event_id`| `UUID` | NO | FK -> `safety_events.id` ON DELETE RESTRICT | Source safety event |
| `case_id` | `UUID` | NO | FK -> `cases.id` ON DELETE RESTRICT | Target case |
| `therapist_id` | `UUID` | NO | FK -> `therapists.id` ON DELETE RESTRICT | Alert recipient clinician |
| `severity` | `VARCHAR(32)` | NO | `'CRITICAL'`, CHECK in (`'CRITICAL'`, `'URGENT'`, `'HIGH'`) | Alert priority tier |
| `status` | `VARCHAR(32)` | NO | `'new'`, CHECK in (`'new'`, `'acknowledged'`, `'escalated'`, `'resolved'`) | Alert lifecycle status |
| `resolution_notes`| `TEXT` | YES | `NULL` | Clinician sign-off commentary |
| `created_at` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Trigger timestamp |
| `acknowledged_at`| `TIMESTAMPTZ` | YES | `NULL` | Clinician acknowledgment time |
| `resolved_at` | `TIMESTAMPTZ` | YES | `NULL` | Resolution timestamp |

### 19.19. `audit_logs`
| Column | Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` PK | Audit event identifier |
| `actor_id` | `UUID` | YES | FK -> `users.id` ON DELETE SET NULL | Performing user (NULL if system) |
| `role` | `VARCHAR(32)` | NO | None | Actor role at time of action |
| `action` | `VARCHAR(100)` | NO | None | Action verb (e.g. `'VIEW_CASE'`) |
| `target_resource`| `VARCHAR(100)`| NO | None | Entity class (e.g. `'Case'`) |
| `target_id` | `VARCHAR(255)` | YES | `NULL` | Entity primary key |
| `ip_address` | `VARCHAR(45)` | YES | `NULL` | IPv4 or IPv6 client address |
| `metadata_payload`| `JSONB` | YES | `NULL` | Sanitized context parameters |
| `timestamp` | `TIMESTAMPTZ` | NO | `CURRENT_TIMESTAMP` | Action timestamp |

---

## 20. Datatypes

1. **Identifiers**: All primary keys use `UUID` with PostgreSQL `gen_random_uuid()` default. Avoids sequential integer exposure and simplifies distributed ID generation.
2. **Strings**: 
   - Strict `VARCHAR(length)` for bounded tokens (`email`, `role`, `status`, `victim_id`, `event_id`, `question_id`).
   - `TEXT` for unbound clinical notes, conversational message bodies, journal text, and error traces.
3. **Numbers**:
   - `DOUBLE PRECISION` for all floating-point ML outputs (DDS, specialist scores, probabilities).
   - `INTEGER` for sequential indexes (`timepoint`, `turn_index`, `reprocessing_version`, `future_escalation_flag`).
4. **Booleans**: Native PostgreSQL `BOOLEAN` (`TRUE` / `FALSE`) for flags (`is_active`, `temporal_available`, `struct_available`, `text_available`, `voice_available`, `behav_available`).
5. **JSONB**: Binary JSON (`JSONB`) for unstructured or polymorphic payloads (`state_payload`, `metadata_payload`, `features_extracted`, `sentiment_metadata`). Supports fast indexing via GIN indexes where required.
6. **Timestamps**: All timestamps strictly use `TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`). Client inputs must be normalized to UTC at the API boundary before persistence.

---

## 21. Constraints

1. **Primary Keys**: Every table has an explicit `id UUID PRIMARY KEY`.
2. **Foreign Keys**: All cross-table references enforce explicit referential integrity with defined `ON DELETE` rules (see Section 24).
3. **Uniqueness Constraints**:
   - `users.email`
   - `therapists.license_number`
   - `cases.victim_id`
   - `chat_sessions.session_identifier`
   - `checkin_answers.checkin_question_id`
   - `behaviour_events.event_id`
   - `predictions(case_id, timepoint)`
   - `structured_features(case_id, timepoint, feature_name)`
4. **Partial Unique Indexes**:
   - `cases(user_id) WHERE status = 'active'`
   - `checkin_sessions(case_id, timepoint) WHERE status = 'completed'`
5. **Check Constraints**:
   - `users.role IN ('user', 'therapist', 'admin')`
   - `cases.current_timepoint >= 1`
   - `cases.status IN ('active', 'closed', 'on_hold')`
   - `chat_sessions.timepoint >= 1`
   - `chat_sessions.status IN ('active', 'completed', 'abandoned')`
   - `chat_messages.role IN ('user', 'assistant', 'system')`
   - `medha_state_snapshots.turn_index >= 0`
   - `checkin_sessions.status IN ('pending', 'in_progress', 'completed', 'missed')`
   - `structured_features`: `CHECK (NOT (numeric_value IS NOT NULL AND categorical_value IS NOT NULL))`
   - `voice_metadata.processing_status IN ('pending', 'processed', 'failed')`
   - `predictions.fusion_dds >= 0.0 AND predictions.fusion_dds <= 100.0`
   - `predictions.temporal_risk IS NULL OR (predictions.temporal_risk >= 0.0 AND predictions.temporal_risk <= 1.0)`
   - `predictions.future_escalation_flag IS NULL OR predictions.future_escalation_flag IN (0, 1)`
   - `predictions.priority_level IS NULL OR predictions.priority_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')`
   - `alerts.severity IN ('CRITICAL', 'URGENT', 'HIGH')`
   - `alerts.status IN ('new', 'acknowledged', 'escalated', 'resolved')`

---

## 22. Indexes

Every index in this schema exists to satisfy an explicit application query or background worker workload:

| Table | Index Name | Columns | Intended Query / Workload Justification |
| :--- | :--- | :--- | :--- |
| `users` | `idx_users_email` | `(email)` | Fast user authentication lookup by email |
| `cases` | `idx_cases_therapist_status` | `(therapist_id, status)` | Fast loading of therapist clinical case roster |
| `cases` | `idx_cases_user_active` | `(user_id) WHERE status = 'active'` | Fast patient app active case retrieval & single active case invariant |
| `cases` | `idx_cases_victim_id` | `(victim_id)` | Fast lookup of case by V2 `Victim_ID` string |
| `chat_sessions` | `idx_chat_sessions_case_tp` | `(case_id, timepoint)` | Session history retrieval by case and timepoint |
| `chat_messages` | `idx_messages_session_time` | `(chat_session_id, timestamp ASC)` | Chronological message retrieval for chat replay & LLM prompt |
| `medha_state_snapshots`| `idx_snapshots_session_created` | `(chat_session_id, created_at DESC)`| Immediate retrieval of latest `MedhaState` snapshot for state restoration |
| `checkin_sessions` | `idx_checkins_case_status` | `(case_id, status)` | Check if an active check-in is pending for patient |
| `checkin_questions`| `idx_checkin_questions_sess` | `(checkin_session_id)` | Loading questions belonging to a check-in session |
| `structured_features` | `idx_struct_feats_case_tp` | `(case_id, timepoint)` | Fast extraction of all features for V2 input DataFrame assembly |
| `behaviour_events` | `idx_behav_events_case_time` | `(case_id, timestamp)` | Window-based behavioral metric calculation (24h, 7d intervals) |
| `predictions` | `idx_predictions_case_tp` | `(case_id, timepoint ASC)` | Fast retrieval of complete longitudinal prediction sequence for GRU |
| `prediction_history`| `idx_pred_hist_canonical_tp` | `(prediction_id, timepoint)` | Audit history retrieval for reprocessed prediction records |
| `alerts` | `idx_alerts_therapist_status` | `(therapist_id, status)` | Primary therapist alert notification queue |
| `alerts` | `idx_alerts_case_status` | `(case_id, status)` | Badge count of unresolved alerts on case summary |
| `alerts` | `idx_alerts_safety_event` | `(safety_event_id)` | Fast lookup of all alerts generated from a safety event |
| `safety_events` | `idx_safety_events_case_time` | `(case_id, timestamp DESC)` | Clinical review of acute safety events for a patient |
| `audit_logs` | `idx_audit_logs_actor_time` | `(actor_id, timestamp DESC)` | Security audits of specific clinician actions |
| `audit_logs` | `idx_audit_logs_target` | `(target_resource, target_id)` | Compliance trace of all actions performed on a specific case/resource |

---

## 23. Relationships

```text
users 1 ──0..1── therapists (PK-to-PK extension)
users 1 ──1..N── cases (Patient ownership)
therapists 1 ──0..N── cases (Assigned primary clinician)
cases 1 ──0..N── case_assignments (Reassignment history)
cases 1 ──0..N── chat_sessions
chat_sessions 1 ──0..N── chat_messages
chat_sessions 1 ──0..N── medha_state_snapshots
cases 1 ──0..N── checkin_sessions
checkin_sessions 1 ──0..N── checkin_questions
checkin_questions 1 ──0..1── checkin_answers
cases 1 ──0..N── structured_features
cases 1 ──0..N── behaviour_events
cases 1 ──0..N── voice_metadata
cases 1 ──0..N── journal_entries
cases 1 ──0..N── predictions
predictions 1 ──0..N── prediction_history
cases 1 ──0..N── safety_events
chat_sessions 1 ──0..N── safety_events
safety_events 1 ──0..N── alerts
therapists 1 ──0..N── alerts
users 1 ──0..N── audit_logs
```

---

## 24. Delete / Retention Semantics (Fix #5 & Fix #6)

Accidental cascading deletion of clinical records is strictly prevented by default:

| Table | Hard Delete Policy | Foreign Key Behavior | Retention & Compliance Mandate |
| :--- | :--- | :--- | :--- |
| `users` | **FORBIDDEN** | `ON DELETE RESTRICT` from cases & therapists | Soft delete via `is_active = FALSE`. Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `therapists` | **FORBIDDEN** | `ON DELETE RESTRICT` from cases & alerts | Therapists cannot be deleted if historical clinical cases or alerts reference them. |
| `cases` | **FORBIDDEN** | `ON DELETE RESTRICT` from all children | Soft delete via `status = 'closed'`. Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `chat_sessions` | **FORBIDDEN** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `chat_messages` | **FORBIDDEN** | `ON DELETE RESTRICT` | Immutable append-only record. Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `medha_state_snapshots`| **PERMITTED (Automated Pruning)** | `ON DELETE CASCADE` from `chat_sessions` | Intermediate turn checkpoints pruned by routine application maintenance process (e.g. 30 days post-session); final session snapshot retained. FK cascade is strictly defensive behavior for administrative cleanup. |
| `checkin_sessions` | **FORBIDDEN** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `checkin_questions`| **PERMITTED on Cascade** | `ON DELETE CASCADE` from `checkin_sessions` | Cascaded only if uncommitted draft checkin is dropped. |
| `checkin_answers` | **FORBIDDEN** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `structured_features`| **RESTRICTED** | `ON DELETE RESTRICT` | Canonical feature history is preserved for model auditability. |
| `behaviour_events` | **APPEND-ONLY** | `ON DELETE RESTRICT` | Cold storage archiving after operational window; never hard deleted online. |
| `voice_metadata` | **METADATA RETAINED** | `ON DELETE RESTRICT` | Extracted JSON metrics retained; raw S3 audio purged after 24h staging window. |
| `journal_entries` | **SOFT DELETE** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `predictions` | **FORBIDDEN** | `ON DELETE RESTRICT` | Immutable clinical AI prediction record. |
| `prediction_history`| **IMMUTABLE** | `ON DELETE RESTRICT` | Never deleted. Full audit trail preserved. |
| `safety_events` | **FORBIDDEN** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. |
| `alerts` | **FORBIDDEN** | `ON DELETE RESTRICT` | Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy. Resolution notes mandatory. |
| `audit_logs` | **IMMUTABLE WRITE-ONCE** | `ON DELETE SET NULL` for actor ID | Append-only. No UPDATE or DELETE grants to application user. Retention period is deployment/compliance policy. |

---

## 25. Missingness Semantics

The MEDHA architecture strictly adheres to the rule: **Missing data is NEVER zero**.

1. **Database Representation**:
   - If a feature is unobserved or unavailable, its column value is **`NULL`**.
   - If a feature is observed and its value is measured as zero, its column value is explicitly **`0.0`**.
2. **Categorical vs. Numeric Exclusivity**:
   In `structured_features`, the CHECK constraint ensures a feature is stored as either numeric or categorical, or both `NULL` (indicating missingness):
   ```sql
   CHECK (NOT (numeric_value IS NOT NULL AND categorical_value IS NOT NULL))
   ```
3. **Application Boundary Translation**:
   When `MedhaV2Adapter` constructs the input DataFrame for `MedhaV2Pipeline.predict_v2()`:
   - Columns where `numeric_value IS NULL` are explicitly populated with `np.nan`.
   - The frozen V2 preprocessors (`v2_structured_dds_preprocessor.pkl`, `v2_behaviour_dds_preprocessor.pkl`) deterministically execute their trained median/mode imputers on these `np.nan` values.
   - Pre-filling unobserved features with `0.0` is strictly forbidden because it corrupts clinical indicators (e.g., zero panic attacks vs. unasked question).

---

## 26. Modality Availability Semantics

### The PostgreSQL Boolean Boundary (Fix #1)

The frozen MEDHA V2 pipeline expects numeric `1.0` or `0.0` in the input DataFrame for `Text_Available` and `Voice_Available` (and hardcodes `Struct_Available = 1.0` and `Behav_Available = 1.0`).

### Database Specification:
In the `predictions` table, the availability flags are defined as:
```sql
struct_available BOOLEAN NOT NULL DEFAULT TRUE,
text_available   BOOLEAN NOT NULL,
voice_available  BOOLEAN NOT NULL,
behav_available  BOOLEAN NOT NULL DEFAULT TRUE
```

### Rationale & Boundary Translation:
- **Database Layer**: `BOOLEAN` is semantically correct, takes 1 byte per flag, enforces strict binary state (`TRUE`/`FALSE`), and eliminates invalid floating-point corruptions (e.g., `0.5`, `2.0`, `NaN`).
- **Adapter Boundary**: When `MedhaV2Adapter` builds the DataFrame for `predict_v2()`:
  ```python
  df["Text_Available"] = 1.0 if state.text_available else 0.0
  df["Voice_Available"] = 1.0 if state.voice_available else 0.0
  df["Struct_Available"] = 1.0
  df["Behav_Available"] = 1.0
  ```
- When `MedhaV2Adapter` extracts predictions from the V2 DataFrame to persist into `predictions`:
  ```python
  prediction_record.text_available = bool(output_row["Text_Available"] == 1.0)
  prediction_record.voice_available = bool(output_row["Voice_Available"] == 1.0)
  prediction_record.struct_available = True
  prediction_record.behav_available = True
  ```

---

## 27. Access-Control Matrix

| Database Entity / Resource | Patient (User Role) | Primary Assigned Therapist | Supervisor / Admin |
| :--- | :--- | :--- | :--- |
| `users` (Self) | Read / Update Profile | Read (Basic bio) | Read / Deactivate |
| `users` (Others) | **NO ACCESS** | **NO ACCESS** | Read / Manage |
| `therapists` Profile | Read-only (Assigned) | Read / Update Self | Full Access |
| `cases` | Read-only (Own active) | Read / Update Status | Full Access |
| `chat_sessions` & `messages`| Read / Create (Own) | Read-only (Assigned case) | Read-only (Audit) |
| `medha_state_snapshots` | **NO ACCESS** (System) | **NO ACCESS** (System) | System Internal |
| `checkin_sessions` & `answers`| Read / Create (Own) | Read-only (Assigned case) | Read-only (Audit) |
| `structured_features` | **NO ACCESS** | Read-only (Assigned case) | Read-only |
| `behaviour_events` | Write-only (Telemetry) | Read-only (Assigned case) | Read-only |
| `voice_metadata` | Create (Own audio) | Read-only (Extracted metrics)| Read-only |
| `journal_entries` | Full CRUD (Own entries)| Read-only (Assigned case) | **NO ACCESS** |
| `predictions` (DDS / Risk) | **STRICTLY FORBIDDEN** | Read-only (Assigned case) | Read-only |
| `prediction_history` | **STRICTLY FORBIDDEN** | Read-only (Assigned case) | Read-only |
| `safety_events` | **STRICTLY FORBIDDEN** | Read-only (Assigned case) | Read-only |
| `alerts` | **STRICTLY FORBIDDEN** | Read / Acknowledge / Resolve | Read / Reassign |
| `audit_logs` | **STRICTLY FORBIDDEN** | **NO ACCESS** | Read-only |

> **CRITICAL CLINICAL FIREWALL:** Under no circumstances shall an API endpoint serialize `predictions`, `fusion_dds`, `temporal_risk`, `future_escalation_flag`, `priority_level`, `safety_events`, or `alerts` to a client authenticated with the `user` (patient) role.

---

## 28. Security & Privacy Considerations

1. **Credential Isolation**:
   - Password hashes reside exclusively in `users.password_hash` using bcrypt.
   - Authentication tokens (JWTs) are stateless or cached in Redis; they are **never** persisted in the database.
2. **PII and Sensitive Data Minimization**:
   - `audit_logs` and `safety_events.evidence` store strictly minimized excerpts. Request headers containing `Authorization` or passwords are stripped before any logging.
3. **Biometric Audio Protection**:
   - Raw voice recordings are temporary artifacts stored in an encrypted S3 bucket with server-side KMS encryption. They are deleted automatically within 24 hours.
4. **Row-Level Case Isolation**:
   - All clinical queries must filter through `cases.therapist_id = :authenticated_therapist_id` or `cases.user_id = :authenticated_user_id`. Therapists cannot query unassigned cases.

---

## 29. V2 Integration Contract

### Exact Data Interface with Frozen Pipeline

```python
# The backend boundary adapter gathers timepoint rows 1 .. T for a case:
# Input DataFrame:
# - Column 'Victim_ID': string matching cases.victim_id
# - Column 'Timepoint': integer sequence 1 .. T
# - 42 Structured Features (columns matching v2_structured_dds_features.json)
# - 10 Behaviour Features (columns matching v2_behaviour_dds_features.json)
# - 5 Text Features + 'Text_Available' (1.0 or 0.0)
# - 5 Voice Features + 'Voice_Available' (1.0 or 0.0)
# - 'Struct_Available': 1.0
# - 'Behav_Available': 1.0

# Inference Call (UNCHANGED, FROZEN):
output_df = pipeline.predict_v2(input_df)

# Target Extraction:
target_row = output_df[
    (output_df["Victim_ID"] == case.victim_id) & 
    (output_df["Timepoint"] == target_timepoint)
].iloc[0]

# Mapping to Database Record:
prediction = Prediction(
    case_id=case.id,
    timepoint=target_timepoint,
    fusion_dds=float(target_row["Fusion_DDS_Prediction"]),
    temporal_risk=float(target_row["Temporal_Risk_Score"]) if pd.notna(target_row["Temporal_Risk_Score"]) else None,
    temporal_available=bool(target_row.get("Temporal_Available", 0) == 1),
    future_escalation_flag=int(target_row["Future_Escalation_Flag"]) if pd.notna(target_row["Future_Escalation_Flag"]) else None,
    struct_pred=float(target_row["Structured_Specialist_DDS"]),
    text_pred=float(target_row["Text_Specialist_DDS"]) if pd.notna(target_row.get("Text_Specialist_DDS")) else None,
    voice_pred=float(target_row["Voice_Specialist_DDS"]) if pd.notna(target_row.get("Voice_Specialist_DDS")) else None,
    behav_pred=float(target_row["Behaviour_Specialist_DDS"]),
    struct_available=True,
    text_available=bool(target_row["Text_Available"] == 1.0),
    voice_available=bool(target_row["Voice_Available"] == 1.0),
    behav_available=True,
    priority_level=priority_info.level,
    priority_rationale=priority_info.rationale,
    pipeline_version="v2.0.0-frozen",
    model_version="v2_frozen_xgb_ridge_gru",
    feature_set_version="canonical_42_5_5_10",
    run_id=uuid.uuid4(),
    reprocessing_version=1,
)
```

---

## 30. Migration Considerations

### Alembic Infrastructure (from Step 3)
- Step 3 established `alembic.ini`, `backend/persistence/migrations/env.py`, and `target_metadata = Base.metadata`.
- **Single Cohesive Initial Migration**: Step 4 will generate migration `001_initial_schema.py` covering the complete schema specified in this document.
- **Dependency Ordering**: Tables must be created in strict foreign key order:
  1. `users`
  2. `therapists`
  3. `cases`
  4. `case_assignments`
  5. `chat_sessions`
  6. `chat_messages`
  7. `medha_state_snapshots`
  8. `checkin_sessions`
  9. `checkin_questions`
  10. `checkin_answers`
  11. `structured_features`
  12. `behaviour_events`
  13. `voice_metadata`
  14. `journal_entries`
  15. `predictions`
  16. `prediction_history`
  17. `safety_events`
  18. `alerts`
  19. `audit_logs`

---

## 31. Final Design Decisions

All 15 review findings and final consistency checks are formally resolved:

1. **Modality Availability Types (Fix #1)**: Persisted as `BOOLEAN NOT NULL`. Mapped to `1.0`/`0.0` at the `MedhaV2Adapter` boundary.
2. **Finalized Timepoint & Mechanisms (Fix #2)**: Unambiguously defined in Section 14. Finalized by either (A) completion of canonical check-in OR (B) authorized explicit/scheduled epoch close when no completed check-in exists. 1-to-1 canonical prediction per timepoint. Multiple chat sessions per timepoint permitted. At most one completed check-in per timepoint.
3. **Verified GRU Window (Fix #3)**: Verified directly in `engine/v2/medha_v2_pipeline.py`. At timepoint $N$, the GRU receives a 7-timestep sequential tensor comprising the 7 strictly prior consecutive timepoints $[N-7, \dots, N-1]$ to predict the temporal risk score for timepoint $N$. Available only when $N \ge 8$.
4. **Prediction Provenance (Fix #3)**: Added `pipeline_version`, `model_version`, `feature_set_version`, `run_id`, `reprocessing_version`, and `computed_at`.
5. **Complete Prediction History (Fix #4)**: `prediction_history` preserves the complete prediction state before overwrite, ensuring 100% auditable longitudinal AI predictions.
6. **Structured Feature Uniqueness (Fix #4)**: Canonical uniqueness established as `UNIQUE(case_id, timepoint, feature_name)`. `source` stored as column metadata.
7. **Structured Feature Value Semantics (Fix #5)**: Missingness represented as both columns `NULL`. Numeric zero stored as `0.0`. Enforced by `CHECK (NOT (numeric_value IS NOT NULL AND categorical_value IS NOT NULL))`.
8. **Retention Policy Language (Fix #5)**: Standardized to "Retention period is deployment/compliance policy and must be configured according to applicable regulations and organizational policy." Safe-by-default foreign key behavior (`RESTRICT`) prevents accidental cascading data loss.
9. **Case Relationships (Fix #6)**: Single primary therapist on `cases.therapist_id`. Reassignments tracked via `case_assignments`. Patient has at most one active case (`UNIQUE(user_id) WHERE status = 'active'`).
10. **MedhaState Delete Semantics (Fix #6 & Fix #7)**: Persisted as native JSON via `to_dict()`/`from_dict()` into `medha_state_snapshots`. Captured per turn checkpoint and session close. Intermediate checkpoints pruned by application maintenance after 30 days. `ON DELETE CASCADE` is defensive behavior for administrative cleanup only.
11. **Prediction Relationship to Inputs (Fix #8)**: Disconnected direct foreign keys from predictions to raw telemetry. Predictions consume timepoint aggregate inputs independently.
12. **Prediction Reprocessing (Fix #9)**: Maintained `UNIQUE(case_id, timepoint)` on canonical `predictions` table. Prior complete runs archived into `prediction_history` with incremented `reprocessing_version`.
13. **Safety Event / Alert Relationship (Fix #10)**: Relaxed to 1-to-many (`SafetyEvent 1 ──< Alerts`). Removed uniqueness constraint on `safety_event_id` to permit supervisor escalations and reassignments.
14. **Voice Storage (Fix #11)**: `s3_reference` is temporary and nullable. Acoustic features extracted to JSON; raw audio purged after 24 hours via S3 lifecycle policy.
15. **Audit Log Privacy (Fix #12)**: Strictly barred passwords, auth tokens, and full message transcripts from audit logs and safety evidence snippets.
16. **Index Review (Fix #13)**: Every single composite index mapped to an explicit query workload in Section 22.
17. **Check-in Lifecycle Consistency (Review Fix #1)**: Unified completely across conceptual and table sections to: `'pending'`, `'in_progress'`, `'completed'`, `'missed'`.
18. **User vs Therapist Access (Fix #15)**: Strict architectural firewall documented in Section 27. Patients never receive predictions, DDS scores, risk metrics, triage levels, or safety event details.

---

## 32. Remaining Open Questions

After exhaustive review of the repository, **ZERO open questions remain that block Step 4 implementation**.

The following non-blocking operational decisions are documented for future deployment stages:
1. **S3 Bucket Lifecycle Expiration Trigger**:
   - *Detail*: Whether S3 objects are purged purely by AWS S3 lifecycle rule (24h) or additionally triggered by an asynchronous backend Celery/FastAPI worker task upon successful extraction.
   - *Resolution*: Schema supports both via nullable `s3_reference` and `processing_status`. Does not block model creation.
2. **Audit Log Cold Storage Partitioning**:
   - *Detail*: PostgreSQL native declarative table partitioning (by year) for `audit_logs` once table exceeds 10 million rows.
   - *Resolution*: Can be applied via future migration without altering table schema contract.

---

## 33. Step 4 Implementation Contract

Step 4 implementation can now proceed with 100% confidence.

### Step 4 Scope Checklist:
- [ ] Create SQLAlchemy 2.0 domain models in `backend/persistence/models/` matching the 19 tables in Section 19.
- [ ] Use `TimestampMixin` from `backend/persistence/base.py` for standard UTC audit fields.
- [ ] Enforce all constraints, foreign keys, `ON DELETE` rules, and check expressions specified herein.
- [ ] Create domain repository abstractions in `backend/persistence/repositories/`.
- [ ] Generate the initial Alembic migration (`001_initial_schema.py`) and verify `alembic upgrade head`.
- [ ] Write comprehensive unit tests for all models, relationships, and constraints in SQLite/PostgreSQL.
- [ ] Maintain absolute zero modifications to `chatbot/` or `engine/`.
