# MEDHA Backend Implementation Plan

## Version

V1.0

## Status

Implementation Plan — Ready for Development

---

# 1. Purpose

This document defines the complete backend architecture and implementation plan for MEDHA.

The backend connects:

- MEDHA User App
- MEDHA Therapist Dashboard
- Authentication and role-based access control
- User/case management
- Existing MEDHA chatbot
- Existing Question Engine
- Existing Safety Trigger / Alert Engine
- Behaviour event collection and aggregation
- Voice processing
- Journal functionality
- Existing frozen MEDHA V2 ML pipeline
- PostgreSQL persistence

The backend is an application/orchestration layer.

It must NOT recreate or modify the existing chatbot or frozen MEDHA V2 engine.

---

# 2. Core Architectural Principle

The architecture is:

Frontend
    ↓
FastAPI Backend
    ↓
Application Services
    ↓
Existing MEDHA Components
    ↓
Frozen MEDHA V2
    ↓
PostgreSQL
    ↓
Therapist Dashboard

The frontend never directly communicates with individual ML models.

The frontend communicates only with backend APIs.

---

# 3. Two Application Roles

MEDHA has two roles.

## 3.1 USER

The user interacts with MEDHA and generates the data.

User capabilities:

- Login
- Onboarding
- Personalisation
- Home
- Quick Check-in
- Follow-up questions
- Voice Check-in
- Chat with MEDHA
- Journal
- Breathing / grounding
- Soundscape
- Support resources
- Notifications
- Profile/settings

Users must NOT see:

- Struct_Pred
- Text_Pred
- Voice_Pred
- Behav_Pred
- Fusion DDS
- Temporal Risk Score
- Future Escalation Flag
- Internal triage/model details
- Internal safety implementation details

---

## 3.2 THERAPIST

The therapist operates the professional dashboard.

Therapist capabilities:

- Login
- Create users
- Create/assign cases
- View assigned users
- View user history
- View check-in history
- View behavioural trends
- View predictions
- View current DDS
- View future risk
- View triage
- View safety alerts
- Review relevant user information according to access policy

A therapist may only access users/cases assigned to that therapist.

---

# 4. User Creation Model

Users are created by therapists.

The primary flow is:

Therapist
    ↓
Create User
    ↓
Backend creates account
    ↓
Backend creates Case
    ↓
User receives credentials
    ↓
User logs in
    ↓
User App

User self-registration is NOT part of the initial backend architecture.

The frontend UI can be changed later to reflect this.

---

# 5. Case-Centric Architecture

A Case is the main ownership boundary for MEDHA data.

Relationship:

Therapist
    │
    ├── Case A ─── User A
    ├── Case B ─── User B
    └── Case C ─── User C

A case owns:

- Sessions
- Messages
- Check-ins
- Questions
- Answers
- Observations
- Structured features
- Voice records
- Behaviour events
- Behaviour features
- Journal entries
- Predictions
- Safety events

This provides a clean boundary for therapist authorization.

---

# 6. Final Repository Structure

MEDHA/
│
├── app.py
│
├── chatbot/
│   ├── conversation_manager.py
│   ├── interfaces.py
│   ├── engines/
│   ├── features/
│   ├── llm/
│   ├── safety/
│   ├── state/
│   ├── summary/
│   ├── v2_adapter/
│   └── tests/
│
├── engine/
│   ├── v2/
│   ├── QuestionEngine/
│   └── ...
│
├── backend/
│   │
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── therapists.py
│   │   ├── cases.py
│   │   ├── sessions.py
│   │   ├── chat.py
│   │   ├── checkin.py
│   │   ├── voice.py
│   │   ├── journal.py
│   │   ├── events.py
│   │   ├── insights.py
│   │   ├── alerts.py
│   │   └── health.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── therapist.py
│   │   ├── case.py
│   │   ├── session.py
│   │   ├── chat.py
│   │   ├── checkin.py
│   │   ├── question.py
│   │   ├── journal.py
│   │   ├── voice.py
│   │   ├── event.py
│   │   ├── prediction.py
│   │   ├── alert.py
│   │   └── common.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── therapist_service.py
│   │   ├── case_service.py
│   │   ├── session_service.py
│   │   ├── chatbot_service.py
│   │   ├── checkin_service.py
│   │   ├── voice_service.py
│   │   ├── journal_service.py
│   │   ├── behaviour_service.py
│   │   ├── prediction_service.py
│   │   ├── alert_service.py
│   │   └── insight_service.py
│   │
│   ├── persistence/
│   │   ├── database.py
│   │   ├── base.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── therapist.py
│   │   │   ├── case.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   ├── checkin.py
│   │   │   ├── question.py
│   │   │   ├── answer.py
│   │   │   ├── observation.py
│   │   │   ├── structured_feature.py
│   │   │   ├── raw_event.py
│   │   │   ├── behaviour_feature.py
│   │   │   ├── journal.py
│   │   │   ├── voice.py
│   │   │   ├── prediction.py
│   │   │   ├── safety_event.py
│   │   │   └── audit_log.py
│   │   │
│   │   └── repositories/
│   │       ├── user_repository.py
│   │       ├── therapist_repository.py
│   │       ├── case_repository.py
│   │       ├── session_repository.py
│   │       ├── message_repository.py
│   │       ├── checkin_repository.py
│   │       ├── event_repository.py
│   │       ├── feature_repository.py
│   │       ├── prediction_repository.py
│   │       ├── alert_repository.py
│   │       └── audit_repository.py
│   │
│   ├── security/
│   │   ├── authentication.py
│   │   ├── authorization.py
│   │   ├── password.py
│   │   └── tokens.py
│   │
│   ├── workers/
│   │   ├── behaviour_aggregator.py
│   │   ├── prediction_worker.py
│   │   └── alert_worker.py
│   │
│   ├── integrations/
│   │   ├── medha_chatbot.py
│   │   ├── medha_v2.py
│   │   ├── alert_provider.py
│   │   └── storage.py
│   │
│   ├── migrations/
│   │
│   └── tests/
│       ├── api/
│       ├── services/
│       ├── security/
│       ├── repositories/
│       ├── integration/
│       └── conftest.py
│
├── requirements.txt
├── .env
└── ...

---

# 7. Database Schema

## 7.1 users

users
------
id
role
name
mobile
email
password_hash
status
must_change_password
created_at
updated_at
last_login_at

Roles:

USER
THERAPIST

Statuses:

ACTIVE
SUSPENDED
DEACTIVATED

---

## 7.2 therapists

therapists
----------
id
user_id
display_name
created_at
updated_at

user_id references users.id.

---

## 7.3 cases

cases
-----
id
user_id
therapist_id
victim_id
status
created_at
updated_at
closed_at

victim_id is the stable identifier passed to the frozen V2 pipeline.

Internal database UUIDs must not replace the V2 Victim_ID contract.

---

## 7.4 sessions

sessions
--------
id
case_id
started_at
ended_at
status
last_activity_at
created_at

Statuses:

ACTIVE
ENDED
EXPIRED

---

## 7.5 messages

messages
--------
id
session_id
sender_type
content
has_audio
created_at

sender_type:

USER
ASSISTANT

---

## 7.6 checkins

checkins
--------
id
case_id
timepoint
started_at
completed_at
status
created_at

Statuses:

STARTED
IN_PROGRESS
COMPLETED
ABANDONED

---

## 7.7 checkin_questions

checkin_questions
----------------
id
checkin_id
question_id
question_text
intent
priority
asked_at
answered
answered_at
cooldown_until

The Question Engine remains authoritative for question selection.

---

## 7.8 checkin_answers

checkin_answers
---------------
id
question_id
answer_type
answer_value
answered_at

answer_value may be JSONB because different question types can have different response formats.

---

## 7.9 observations

observations
------------
id
case_id
session_id
domain
semantic_value
evidence
source
created_at

Observations are qualitative evidence.

They must not automatically become numerical structured features.

---

## 7.10 structured_features

structured_features
------------------
id
case_id
timepoint
feature_name
feature_value
source
source_reference
recorded_at

Missing values remain NULL.

Do not replace missing values with 0.

---

## 7.11 raw_events

raw_events
----------
id
event_id
case_id
session_id
event_type
screen
occurred_at
received_at
metadata

event_id must be unique for idempotency.

---

## 7.12 behaviour_features

behaviour_features
------------------
id
case_id
timepoint

App_Interaction_Duration
App_Interaction_Duration_Deviation
Checkin_Response_Delay
Checkin_Response_Delay_Deviation
Checkin_Completion_Rate
Missed_Checkin_Count
Journal_Entry_Count
Chat_Message_Count
Late_Night_Usage_Ratio
Support_Resource_Access_Count

window_start
window_end
computed_at

---

## 7.13 voice_records

voice_records
-------------
id
case_id
session_id
timepoint
processed_at
available

Raw audio should be temporary unless there is an explicit justified storage requirement.

---

## 7.14 voice_features

voice_features
--------------
id
case_id
timepoint
feature_name
feature_value

---

## 7.15 journal_entries

journal_entries
---------------
id
case_id
content
created_at
updated_at

---

## 7.16 predictions

predictions
-----------
id
case_id
timepoint

Struct_Pred
Text_Pred
Voice_Pred
Behav_Pred

Struct_Available
Text_Available
Voice_Available
Behav_Available

Fusion_DDS_Prediction

Temporal_Risk_Score
Temporal_Available
Future_Escalation_Flag

triage_level

generated_at
model_version

Predictions are therapist-only data.

---

## 7.17 safety_events

safety_events
-------------
id
case_id
session_id
event_type
severity
detected_at
status
payload
handled_at
handled_by

Safety event types include:

immediate_danger
self_harm_intent
suicidal_intent
threat_to_other
immediate_protection_concern

---

## 7.18 audit_logs

audit_logs
----------
id
actor_user_id
actor_role
action
resource_type
resource_id
timestamp
metadata

Used for sensitive operations such as:

THERAPIST_CREATED_USER
THERAPIST_VIEWED_PREDICTION
THERAPIST_VIEWED_ALERT
USER_LOGIN
THERAPIST_LOGIN
CASE_UPDATED

---

# 8. API Architecture

All APIs use:

/api/v1/

---

## Authentication

POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me

---

## User

GET   /api/v1/users/me
PATCH /api/v1/users/me

---

## Therapist

GET  /api/v1/therapist/me
POST /api/v1/therapist/users
GET  /api/v1/therapist/users
GET  /api/v1/therapist/users/{user_id}

---

## Cases

GET   /api/v1/therapist/cases
GET   /api/v1/therapist/cases/{case_id}
PATCH /api/v1/therapist/cases/{case_id}

---

## Chat

POST /api/v1/chat/message
GET  /api/v1/chat/history

The API must call:

ChatbotService
    ↓
ConversationManager

It must not bypass ConversationManager.

---

## Check-in

POST /api/v1/checkins
GET  /api/v1/checkins/{checkin_id}
GET  /api/v1/checkins/{checkin_id}/next
POST /api/v1/checkins/{checkin_id}/answer
POST /api/v1/checkins/{checkin_id}/complete

---

## Voice

POST /api/v1/voice/checkin

---

## Journal

POST /api/v1/journal
GET  /api/v1/journal
GET  /api/v1/journal/{id}
PATCH /api/v1/journal/{id}

---

## Behaviour

POST /api/v1/events/batch

---

## Therapist Predictions

GET /api/v1/therapist/cases/{case_id}/predictions/latest

GET /api/v1/therapist/cases/{case_id}/predictions/history

GET /api/v1/therapist/cases/{case_id}/behaviour

GET /api/v1/therapist/cases/{case_id}/checkins

GET /api/v1/therapist/cases/{case_id}/alerts

---

# 9. Core Data Flow

## Chat

User
 ↓
POST /chat/message
 ↓
ChatbotService
 ↓
ConversationManager
 ↓
Safety Trigger
 ↓
Behaviour Adapter
 ↓
Voice Adapter if applicable
 ↓
Safety Gateway
 ↓
Text Engine
 ↓
Question Engine
 ↓
Summary Engine
 ↓
LLM
 ↓
Feature Mapper
 ↓
MedhaState
 ↓
Persistence
 ↓
Response to User

---

# 10. Check-in Flow

User starts check-in.

POST /checkins
 ↓
CheckinService
 ↓
Create Checkin
 ↓
Question Engine
 ↓
QuestionRecord
 ↓
Frontend displays question

User answers.

POST /checkins/{id}/answer
 ↓
Validate answer
 ↓
Persist answer
 ↓
Update authoritative structured feature
 ↓
Mark QuestionRecord answered
 ↓
Generate behaviour event
 ↓
Question Engine selects next question
 ↓
Continue or complete

---

# 11. Behaviour Flow

Frontend
 ↓
POST /events/batch
 ↓
Raw Event Log
 ↓
Behaviour Aggregator
 ↓
10 Behaviour Features
 ↓
Behaviour Specialist
 ↓
Behav_Pred
 ↓
V2 Fusion

The frontend only reports events.

It does not calculate behavioural features.

---

# 12. V2 Flow

Backend
 ↓
MedhaV2Adapter
 ↓
Construct exact V2 DataFrame
 ↓
Validate Victim_ID
 ↓
Validate Timepoint
 ↓
Validate feature whitelist/order
 ↓
Preserve missing values
 ↓
Run frozen MEDHA V2
 ↓
Store predictions

V2 remains unchanged.

---

# 13. Missingness Rules

Missing does NOT mean zero.

Examples:

No voice:

Voice_Available = 0
Voice_Pred = 0 or model-defined missing representation according to frozen contract

But an unavailable structured feature must remain missing.

At the DataFrame boundary:

missing → NaN

Never:

missing → 0

---

# 14. Security Rules

## Authentication

All protected endpoints require authentication.

## Authorization

Every protected resource must verify:

1. authenticated user
2. role
3. case ownership/assignment

## User restrictions

Users cannot access:

/therapist/*
predictions
other users
other cases

## Therapist restrictions

Therapists can only access assigned cases.

## Passwords

Never store plaintext passwords.

Store password hashes only.

## Secrets

Gemini/API/database credentials remain server-side.

Never send secrets to frontend.

---

# 15. Privacy Rules

The user sees conversational/wellness functionality.

The therapist sees authorized professional results.

The frontend must never receive internal model reasoning.

Do not expose:

- raw model internals
- feature engineering implementation
- internal safety trigger logic
- model reasoning
- hidden classification details

unless explicitly required by a future approved therapist-facing contract.

---

# 16. Background Processing

Initially:

Synchronous:
- Chat
- Check-in
- Voice processing
- V2 inference

Background:
- Behaviour aggregation
- Alert delivery
- Other non-critical heavy operations

The architecture should allow prediction processing to become asynchronous later without redesigning the public API.

---

# 17. Technology

Backend:

FastAPI

Language:

Python

Database:

PostgreSQL

ORM:

SQLAlchemy

Migrations:

Alembic

Validation:

Pydantic

Authentication:

JWT/session-based authentication

Password hashing:

Argon2/bcrypt-compatible secure hashing

Testing:

pytest

Architecture:

Modular monolith

---

# 18. Frozen Components

The following existing systems are treated as authoritative:

- chatbot/conversation_manager.py
- chatbot/interfaces.py
- chatbot/engines/
- chatbot/features/
- chatbot/llm/
- chatbot/safety/
- chatbot/state/
- chatbot/summary/
- chatbot/v2_adapter/
- engine/
- existing Question Engine
- existing MEDHA V2 models/pipelines

Backend integration must wrap these systems.

It must not recreate them.

---

# 19. Implementation Phases

---

# PHASE 1 — Repository Audit and Backend Foundation

## Step 1 — Repository Audit

### Goal

Understand the existing repository before writing backend code.

### Antigravity Prompt

You are implementing the MEDHA backend.

Before changing anything, inspect the complete repository and the existing MEDHA architecture documentation.

You must specifically inspect:

- chatbot/
- engine/
- chatbot/conversation_manager.py
- chatbot/interfaces.py
- chatbot/state/
- chatbot/safety/
- chatbot/features/
- chatbot/v2_adapter/
- engine/QuestionEngine/
- existing tests
- existing requirements/dependencies
- existing configuration

Determine:

1. How the current chatbot is instantiated.
2. How ConversationManager sessions currently work.
3. How MedhaState is created and updated.
4. How Question Engine is called.
5. How Safety Trigger and Alert Engine are exposed.
6. How Voice Adapter works.
7. How Behaviour Adapter works.
8. How Feature Mapper works.
9. How MedhaV2Adapter works.
10. How the frozen V2 pipeline is invoked.
11. Existing dependency/configuration patterns.

Do NOT modify any frozen engine code.

Do NOT implement the backend yet.

Create:

backend/AUDIT.md

containing:

- existing architecture findings
- integration points
- dependencies
- risks
- files that must remain untouched
- recommended backend integration boundaries

Run the existing test suite if possible.

At the end report:

- files inspected
- tests run
- findings
- files changed

STOP after the audit.

Do not proceed to Phase 1 Step 2 automatically.

---

# Step 2 — FastAPI Foundation

### Goal

Create the basic backend application.

### Prompt

Implement the MEDHA backend foundation.

First read:

- backend/AUDIT.md
- MEDHA backend implementation plan
- existing repository architecture

Create:

backend/
    main.py
    config.py
    dependencies.py
    api/
    schemas/
    services/
    persistence/
    security/
    workers/
    integrations/
    tests/

Implement:

- FastAPI application
- /api/v1 router
- configuration management
- environment variable loading
- health endpoint
- readiness endpoint
- basic error handling
- CORS configuration suitable for development
- logging configuration

Do NOT implement authentication yet.

Do NOT modify chatbot/ or engine/.

Create tests for:

- application startup
- health endpoint
- readiness endpoint
- API version routing

Run tests.

Report changed files and test results.

STOP.

---

# Step 3 — PostgreSQL + SQLAlchemy + Alembic

### Goal

Establish persistence infrastructure.

### Prompt

Implement the MEDHA database foundation.

Use:

- PostgreSQL
- SQLAlchemy
- Alembic

Create:

backend/persistence/database.py
backend/persistence/base.py
backend/persistence/models/
backend/persistence/repositories/

Configure:

- database URL
- SQLAlchemy engine
- session factory
- declarative base
- dependency for DB sessions
- Alembic migrations

Do not implement the complete business schema yet.

Create only the infrastructure necessary to support later models.

Add:

- database connection test
- migration test/setup
- development instructions

Do NOT modify chatbot/ or engine/.

Run tests.

STOP after this step.

---

# PHASE 2 — Authentication and RBAC

# Step 4 — User and Therapist Models

### Prompt

Implement the account foundation for MEDHA.

Create SQLAlchemy models for:

users
therapists

Users must contain:

- id
- role
- name
- mobile
- email
- password_hash
- status
- must_change_password
- created_at
- updated_at
- last_login_at

Roles:

USER
THERAPIST

Statuses:

ACTIVE
SUSPENDED
DEACTIVATED

Therapist must reference its authentication user.

Add migrations.

Add Pydantic schemas.

Add repositories.

Do not implement login yet.

Do not modify chatbot/ or engine/.

Test relationships and constraints.

STOP.

---

# Step 5 — Password Hashing and Authentication

### Prompt

Implement secure MEDHA authentication.

Implement:

- password hashing
- password verification
- login service
- JWT/token generation
- token validation
- current-user dependency
- logout/token invalidation strategy appropriate to the current architecture

Never store plaintext passwords.

Implement:

POST /api/v1/auth/login
GET /api/v1/auth/me
POST /api/v1/auth/refresh
POST /api/v1/auth/logout

Authentication must identify:

- user_id
- role

Add tests for:

- valid login
- invalid password
- inactive account
- token validation
- expired token
- authenticated endpoint

Do not implement therapist authorization yet.

Do not modify chatbot/ or engine/.

STOP.

---

# Step 6 — RBAC and Case Authorization Foundation

### Prompt

Implement MEDHA role-based authorization.

Create:

backend/security/authorization.py

Implement dependencies/helpers for:

- authenticated user
- require USER
- require THERAPIST
- therapist-case ownership verification

The critical rule is:

A therapist may access only cases assigned to that therapist.

A user may access only their own case.

Users must never access therapist endpoints.

Add tests for:

- USER → user endpoint allowed
- THERAPIST → therapist endpoint allowed
- USER → therapist endpoint denied
- Therapist A → Therapist B case denied
- Therapist → assigned case allowed

Do not implement the complete case API yet.

STOP.

---

# PHASE 3 — Users and Cases

# Step 7 — Therapist Creates Users

### Prompt

Implement therapist-created user accounts.

Create:

POST /api/v1/therapist/users
GET /api/v1/therapist/users
GET /api/v1/therapist/users/{user_id}

Only THERAPIST may access these endpoints.

When creating a user:

1. validate input
2. create USER account
3. securely generate/store password hash
4. mark must_change_password if appropriate
5. create associated case
6. generate stable Victim_ID
7. associate case with therapist
8. return safe account information

Never return password hashes.

Never expose internal security data.

Implement repositories, services, schemas, authorization, migrations, and tests.

Test therapist isolation.

Do not modify V2.

STOP.

---

# Step 8 — Case Management

### Prompt

Implement MEDHA case management.

Create:

GET /api/v1/therapist/cases
GET /api/v1/therapist/cases/{case_id}
PATCH /api/v1/therapist/cases/{case_id}

Implement:

- case retrieval
- case status
- therapist assignment
- user association
- Victim_ID handling
- authorization

Every case query must enforce therapist ownership.

A therapist must never be able to access another therapist's case.

Add audit logs for sensitive case modifications.

Run security tests.

STOP.

---

# PHASE 4 — Sessions and MedhaState

# Step 9 — Persistent Sessions

### Prompt

Implement persistent MEDHA sessions.

Create:

sessions model
session repository
session service

Implement:

- create session
- get active session
- end session
- session expiration
- last activity tracking

Sessions belong to Cases.

Then design the bridge between persisted sessions and the existing MedhaState.

Do not delete or rewrite ConversationManager.

Do not modify frozen chatbot logic unless a minimal integration adapter is required.

The backend must be able to:

Database
 ↓
load session state
 ↓
construct MedhaState
 ↓
ConversationManager
 ↓
persist relevant state

Add tests.

STOP.

---

# PHASE 5 — Chatbot Integration

# Step 10 — Chatbot Service

### Prompt

Integrate the existing MEDHA chatbot into the backend.

Create:

backend/services/chatbot_service.py
backend/integrations/medha_chatbot.py
backend/api/chat.py
backend/schemas/chat.py

The backend must call the existing ConversationManager.

Do NOT recreate:

- safety logic
- Question Engine
- text engine
- feature mapper
- summary engine
- LLM orchestration

The service should:

1. authenticate user
2. resolve case
3. resolve/create session
4. load required MedhaState
5. call ConversationManager
6. persist messages
7. persist observations
8. persist safety events
9. persist relevant state
10. return a safe user-facing response

Implement:

POST /api/v1/chat/message
GET /api/v1/chat/history

Do not expose model predictions.

Add integration tests.

STOP.

---

# Step 11 — Safety Integration

### Prompt

Integrate the existing MEDHA Safety Trigger and Alert Engine with the backend.

Inspect the existing:

- Safety Trigger
- Safety Gateway
- AlertEngineProtocol
- MockAlertEngine

Do not replace existing safety logic.

Implement backend persistence for safety events.

Implement AlertService and Alert Worker integration.

Safety alerts must be:

- non-blocking
- asynchronous where appropriate
- persisted
- auditable
- isolated from normal chat failure

An alert delivery failure must never crash a normal chat request.

Add tests for:

- safety event persistence
- duplicate event handling
- alert failure
- normal chat continuing when alert delivery fails

STOP.

---

# PHASE 6 — Question Engine + Check-in

# Step 12 — Question Engine Integration

### Prompt

Integrate the existing Question Engine into the backend check-in architecture.

The Question Engine remains the authority for:

- missing feature detection
- candidate observation suppression
- priority
- cooldown
- question selection
- one-question-per-turn behavior

Do NOT duplicate Question Engine logic.

Create an integration wrapper only where required.

The wrapper must convert backend persisted state into the inputs expected by the existing Question Engine.

Test:

- missing feature
- candidate observation suppression
- cooldown
- priority
- one question maximum

STOP.

---

# Step 13 — Check-in Persistence

### Prompt

Implement check-in persistence.

Create models:

checkins
checkin_questions
checkin_answers

Create:

CheckinService
CheckinRepository
schemas
API routes

Implement:

POST /api/v1/checkins
GET /api/v1/checkins/{checkin_id}
GET /api/v1/checkins/{checkin_id}/next
POST /api/v1/checkins/{checkin_id}/answer
POST /api/v1/checkins/{checkin_id}/complete

Check-in flow:

create check-in
 ↓
Question Engine
 ↓
QuestionRecord
 ↓
persist question
 ↓
return question
 ↓
user answers
 ↓
persist answer
 ↓
update authoritative structured feature
 ↓
mark question answered
 ↓
generate behaviour event
 ↓
select next question

Do not modify the Question Engine.

STOP.

---

# Step 14 — Structured Feature Persistence

### Prompt

Implement authoritative structured feature persistence.

Create:

structured_features model
repository
service
schemas

Features must include:

- feature_name
- feature_value
- source
- source_reference
- case_id
- timepoint

Preserve missingness.

Never convert missing values to zero.

Only approved authoritative sources may update numerical structured features.

Candidate qualitative observations must remain separate.

Add tests for:

- valid feature
- missing feature
- update
- multiple timepoints
- source tracking
- no accidental observation-to-number conversion

STOP.

---

# PHASE 7 — Behaviour Pipeline

# Step 15 — Event Ingestion

### Prompt

Implement the MEDHA behaviour event ingestion API.

Create:

raw_events model
repository
event schemas
event service
events API

Implement:

POST /api/v1/events/batch

Events must include:

- event_id
- event_type
- screen
- occurred_at
- metadata

Associate events with:

- case
- session

Implement idempotency using event_id.

Duplicate events must not be inserted or counted twice.

Support events such as:

screen_view
session_start
session_end
checkin_started
checkin_prompt_shown
checkin_answered
checkin_completed
journal_opened
journal_saved
voice_started
voice_completed
chat_message_sent
support_opened
notification_tapped
notification_dismissed
app_backgrounded

Do not calculate behavioural features in the API layer.

STOP.

---

# Step 16 — Behaviour Aggregator

### Prompt

Implement the MEDHA behaviour aggregation pipeline.

The aggregator must transform raw events into the existing ten behaviour features:

App_Interaction_Duration
App_Interaction_Duration_Deviation
Checkin_Response_Delay
Checkin_Response_Delay_Deviation
Checkin_Completion_Rate
Missed_Checkin_Count
Journal_Entry_Count
Chat_Message_Count
Late_Night_Usage_Ratio
Support_Resource_Access_Count

Important:

- aggregation owns deviation calculations
- raw events remain immutable
- duplicate events must not inflate counts
- late-arriving events must be handled
- cold-start cases must be handled
- zero activity must be handled
- missing data must remain semantically distinct from zero

Persist results to behaviour_features.

Add tests for:

- cold start
- zero activity
- duplicate events
- late events
- baseline/deviation calculations
- multiple timepoints

STOP.

---

# PHASE 8 — Voice and Journal

# Step 17 — Voice Integration

### Prompt

Integrate the existing Voice Adapter into the backend.

Create:

voice API
voice service
voice integration adapter
voice schemas
voice persistence

Implement:

POST /api/v1/voice/checkin

Flow:

audio upload
 ↓
temporary storage
 ↓
Voice Adapter
 ↓
voice features
 ↓
Voice_Pred
 ↓
V2 integration
 ↓
delete temporary raw audio

Do not expose internal model details.

Do not permanently store raw audio unless explicitly required.

Add cleanup and failure tests.

STOP.

---

# Step 18 — Journal

### Prompt

Implement the journal backend.

Create:

journal_entries model
repository
service
schemas
API routes

Implement:

POST /api/v1/journal
GET /api/v1/journal
GET /api/v1/journal/{id}
PATCH /api/v1/journal/{id}

Users can only access their own journal entries.

Therapist access must follow the final privacy policy and must not be assumed to mean unrestricted raw journal access.

Persist journal activity as appropriate for behaviour telemetry.

Do not automatically convert arbitrary journal content into structured numerical features.

Add authorization tests.

STOP.

---

# PHASE 9 — MEDHA V2 Integration

# Step 19 — V2 Integration Adapter

### Prompt

Integrate the existing frozen MEDHA V2 pipeline into the backend.

First inspect:

- chatbot/v2_adapter/
- engine/
- existing V2 pipeline
- current V2 tests
- frozen V2 documentation

Do NOT change:

- model architecture
- weights
- feature order
- feature whitelist
- GRU setup
- fusion architecture
- scaler behavior
- thresholds
- train/test logic

Create backend integration around the existing adapter.

The backend must construct valid V2 input using:

Victim_ID
Timepoint
Structured features
Text features
Voice features
Behaviour features
Availability flags

Validate the exact feature contract before inference.

STOP if the existing V2 contract is unclear.

Do not guess.

---

# Step 20 — Prediction Service

### Prompt

Implement PredictionService.

PredictionService must:

1. resolve case
2. determine current timepoint
3. load structured features
4. load text-derived features
5. load voice features
6. load behaviour features
7. determine modality availability
8. construct V2 input
9. call existing MedhaV2Adapter
10. receive V2 result
11. persist prediction
12. return an internal prediction object

Do not expose predictions to USER APIs.

Handle unavailable modalities according to the frozen V2 contract.

Do not fake historical data for the GRU.

If seven valid historical timesteps are unavailable:

Temporal_Risk_Score must remain unavailable according to the existing V2 contract.

STOP.

---

# Step 21 — Triage Service

### Prompt

Implement the backend triage service around the existing V2 outputs.

Do not alter frozen V2 calculations.

Use the already-approved triage thresholds.

The service must distinguish:

- current DDS
- future risk
- triage level
- temporal availability

Persist therapist-facing triage information.

Add tests for every threshold boundary.

Do not expose triage to USER endpoints.

STOP.

---

# PHASE 10 — Therapist Results

# Step 22 — Therapist Prediction APIs

### Prompt

Implement therapist-only prediction APIs.

Create:

GET /api/v1/therapist/cases/{case_id}/predictions/latest
GET /api/v1/therapist/cases/{case_id}/predictions/history

Only THERAPIST may access them.

Every request must verify case assignment.

Return therapist-oriented prediction data.

Include only approved fields:

- timepoint
- current DDS
- future risk
- future escalation flag
- triage
- temporal availability
- generation timestamp
- model version
- approved specialist outputs if required

Add security tests proving:

USER cannot access predictions.

Therapist A cannot access Therapist B's predictions.

STOP.

---

# Step 23 — Therapist Behaviour and Check-in APIs

### Prompt

Implement therapist-facing historical APIs.

Create:

GET /api/v1/therapist/cases/{case_id}/behaviour
GET /api/v1/therapist/cases/{case_id}/checkins

Only assigned therapists can access these endpoints.

Return structured therapist-facing historical data.

Do not expose unnecessary raw implementation details.

Add authorization tests.

STOP.

---

# Step 24 — Therapist Alerts

### Prompt

Implement therapist-facing safety alert APIs.

Create:

GET /api/v1/therapist/cases/{case_id}/alerts

Only assigned therapists can access alerts.

Implement:

- alert status
- created time
- severity
- event type
- handling state
- handled_by
- handled_at

Add audit logging when a therapist views or updates an alert.

Do not modify Safety Trigger logic.

STOP.

---

# PHASE 11 — Insights and Supporting APIs

# Step 25 — Insights Service

### Prompt

Implement the therapist-facing insight aggregation layer.

Create InsightService.

It should aggregate existing persisted information such as:

- check-in history
- prediction history
- behaviour trends
- alert history
- approved longitudinal information

Do not create a new ML model.

Do not reinterpret V2 predictions.

Do not expose unsupported clinical conclusions.

Keep insights descriptive and based only on stored approved data.

STOP.

---

# Step 26 — Notifications

### Prompt

Implement the backend notification foundation.

Support notification records associated with:

- user
- case
- notification type
- message
- created_at
- read_at

Do not implement complex push infrastructure unless the existing frontend requires it.

The initial implementation may provide database/API support only.

Ensure notification activity can produce behaviour telemetry.

STOP.

---

# PHASE 12 — Security and Hardening

# Step 27 — Authorization Audit

### Prompt

Perform a complete authorization audit of the MEDHA backend.

Test every protected endpoint.

Verify:

USER:
- can access own data
- cannot access therapist APIs
- cannot access predictions
- cannot access another user
- cannot access another case

THERAPIST:
- can access assigned users
- can access assigned cases
- can access assigned predictions
- cannot access another therapist's case
- cannot modify another therapist's case

Fix any authorization vulnerability found.

Do not modify frozen ML components.

Run the complete security test suite.

STOP.

---

# Step 28 — Data Privacy Audit

### Prompt

Perform a MEDHA data privacy audit.

Search the entire backend for accidental exposure of:

- DDS
- Future Risk
- model reasoning
- model internals
- safety internals
- password hashes
- API keys
- secrets
- raw audio
- unauthorized user data

Verify response schemas.

Verify logging does not leak sensitive information.

Verify frontend USER endpoints cannot return therapist-only prediction fields.

Create:

backend/PRIVACY_AUDIT.md

Report all findings and fixes.

STOP.

---

# Step 29 — Audit Logging

### Prompt

Complete the MEDHA audit logging system.

Audit sensitive operations including:

- login
- therapist-created user
- case creation
- case assignment
- case update
- therapist prediction access
- therapist alert access
- alert handling
- account status changes

Audit logs must contain:

- actor
- role
- action
- resource
- resource_id
- timestamp
- metadata where appropriate

Do not store sensitive content unnecessarily.

Add tests.

STOP.

---

# PHASE 13 — Integration Testing

# Step 30 — End-to-End User Flow

### Prompt

Create an end-to-end integration test for:

Therapist login
 ↓
Create user
 ↓
Create case
 ↓
User login
 ↓
Create session
 ↓
Start check-in
 ↓
Question Engine selects question
 ↓
User answers
 ↓
Structured feature updated
 ↓
Behaviour event recorded
 ↓
Next question selected
 ↓
Check-in completed
 ↓
Chat session started
 ↓
User sends message
 ↓
ConversationManager processes message
 ↓
Response persisted
 ↓
Behaviour event persisted
 ↓
V2 prediction generated where sufficient data exists
 ↓
Therapist retrieves prediction

Use test fixtures.

Do not use real production credentials.

Do not modify frozen models.

STOP.

---

# Step 31 — Security Integration Tests

### Prompt

Create complete security integration tests.

Test:

1. User cannot access therapist dashboard.
2. User cannot access predictions.
3. User cannot access another user's data.
4. Therapist cannot access another therapist's case.
5. Therapist can access assigned case.
6. Invalid JWT rejected.
7. Expired JWT rejected.
8. Suspended account rejected.
9. Password is never returned.
10. Prediction data is never returned by user endpoints.

Run all tests.

STOP.

---

# Step 32 — Behaviour/V2 Integration Tests

### Prompt

Create integration tests for:

raw events
 ↓
behaviour aggregation
 ↓
behaviour features
 ↓
Behaviour specialist
 ↓
V2 Fusion

Also test:

- duplicate events
- missing modality
- missing structured feature
- missing voice
- insufficient GRU history
- valid seven-timestep history
- multiple timepoints

Do not change the V2 implementation to make tests pass.

If an existing V2 contract fails, report it instead of modifying it.

STOP.

---

# PHASE 14 — Deployment Preparation

# Step 33 — Production Configuration

### Prompt

Prepare the MEDHA backend for deployment.

Implement configuration for:

- database URL
- JWT secret
- token expiration
- Gemini configuration
- storage configuration
- CORS origins
- logging
- environment selection

Ensure secrets are loaded from environment variables.

Create:

.env.example

Never commit real secrets.

Add startup/readiness checks.

STOP.

---

# Step 34 — Database Migration Verification

### Prompt

Verify the complete Alembic migration chain.

Start from an empty database.

Run all migrations.

Verify:

- all tables
- foreign keys
- indexes
- unique constraints
- enums
- nullable fields
- timestamps

Then run the application against the migrated database.

Do not modify application logic unless required to fix a genuine migration problem.

STOP.

---

# Step 35 — Final Backend Audit

### Prompt

Perform a complete MEDHA backend audit.

Inspect:

- API structure
- authentication
- authorization
- database
- services
- repositories
- chatbot integration
- Question Engine integration
- behaviour pipeline
- voice integration
- safety system
- V2 integration
- therapist APIs
- privacy
- tests
- configuration
- migrations

Verify the backend follows the MEDHA backend implementation plan.

Verify:

1. Existing chatbot remains authoritative.
2. Question Engine remains authoritative.
3. V2 remains frozen.
4. Backend never directly exposes specialist models.
5. USER and THERAPIST roles are enforced.
6. Therapist ownership isolation works.
7. Predictions are therapist-only.
8. Missingness is preserved.
9. Behaviour events are idempotent.
10. Safety alerts are non-blocking.
11. Sessions can be reconstructed.
12. Complete test suite passes.

Create:

backend/FINAL_BACKEND_AUDIT.md

Include:

- architecture verification
- completed components
- remaining issues
- test results
- security findings
- recommendations

Do not implement new features during this audit.

STOP.

---

# 20. Antigravity Rules

Every prompt above follows these rules.

Antigravity must:

1. Inspect existing code before modifying it.
2. Read relevant MEDHA documentation.
3. Never assume an existing component's interface.
4. Never modify frozen MEDHA V2 unless explicitly instructed.
5. Never duplicate Question Engine logic.
6. Never duplicate ConversationManager logic.
7. Never bypass the existing chatbot architecture.
8. Preserve missingness.
9. Preserve modality availability.
10. Enforce role-based authorization server-side.
11. Enforce therapist-case ownership server-side.
12. Never expose predictions to users.
13. Never store plaintext passwords.
14. Never commit secrets.
15. Run tests after implementation.
16. Report changed files.
17. Report test results.
18. Stop after the requested step.
19. Do not silently implement future phases.
20. If the existing repository contradicts the plan, stop and report the conflict instead of guessing.

---

# 21. Definition of Done

The backend is considered complete when:

## Authentication

- [ ] USER authentication works.
- [ ] THERAPIST authentication works.
- [ ] Passwords are securely hashed.
- [ ] JWT/session authentication works.
- [ ] Account status is enforced.

## RBAC

- [ ] USER permissions enforced.
- [ ] THERAPIST permissions enforced.
- [ ] Cross-therapist access blocked.
- [ ] User prediction access blocked.

## User Management

- [ ] Therapist can create users.
- [ ] User receives credentials.
- [ ] User account is associated with a case.
- [ ] Case is associated with therapist.
- [ ] Stable Victim_ID exists.

## Chat

- [ ] Existing ConversationManager is used.
- [ ] Chat messages persist.
- [ ] MedhaState can be reconstructed.
- [ ] Safety Trigger integrated.
- [ ] Question Engine remains authoritative.
- [ ] LLM remains behind existing chatbot architecture.

## Check-in

- [ ] Check-ins persist.
- [ ] Questions persist.
- [ ] Answers persist.
- [ ] Question Engine selects questions.
- [ ] Structured features update correctly.
- [ ] Behaviour events are generated.

## Behaviour

- [ ] Events are ingested.
- [ ] event_id provides idempotency.
- [ ] Raw events persist.
- [ ] Ten behaviour features are computed.
- [ ] Deviations are calculated correctly.

## Voice

- [ ] Voice endpoint works.
- [ ] Existing Voice Adapter is used.
- [ ] Temporary audio is cleaned.
- [ ] Voice availability is persisted.

## V2

- [ ] Existing V2 adapter is used.
- [ ] Exact feature contract preserved.
- [ ] Missingness preserved.
- [ ] Availability flags preserved.
- [ ] Current DDS works.
- [ ] Future Risk works when sufficient history exists.
- [ ] GRU never receives fabricated history.
- [ ] Predictions are persisted.

## Therapist

- [ ] Therapist can list users.
- [ ] Therapist can view assigned cases.
- [ ] Therapist can view predictions.
- [ ] Therapist can view historical data.
- [ ] Therapist can view alerts.
- [ ] Cross-therapist access is blocked.

## Safety

- [ ] Safety events persist.
- [ ] Alert delivery is isolated.
- [ ] Alert failure cannot crash chat.
- [ ] Therapist can retrieve alerts.

## Security

- [ ] No plaintext passwords.
- [ ] No secrets committed.
- [ ] No prediction leakage to users.
- [ ] No cross-case leakage.
- [ ] Sensitive access is audited.

## Testing

- [ ] Unit tests pass.
- [ ] API tests pass.
- [ ] Security tests pass.
- [ ] Integration tests pass.
- [ ] Behaviour tests pass.
- [ ] V2 integration tests pass.
- [ ] End-to-end flow passes.

---

# 22. Final Architecture

                    ┌───────────────────────┐
                    │       USER APP        │
                    │                       │
                    │ Chat                  │
                    │ Check-in              │
                    │ Voice                 │
                    │ Journal               │
                    │ Behaviour             │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │     FASTAPI BACKEND   │
                    │                       │
                    │ Auth + RBAC           │
                    │ Users + Cases         │
                    │ Sessions              │
                    │ Chat                  │
                    │ Check-ins             │
                    │ Voice                 │
                    │ Journal               │
                    │ Events                │
                    │ Predictions           │
                    │ Alerts                │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
       ┌────────────┐    ┌─────────────┐    ┌──────────────┐
       │  EXISTING  │    │  QUESTION   │    │  BEHAVIOUR   │
       │  CHATBOT   │    │   ENGINE    │    │  AGGREGATOR  │
       │            │    │             │    │              │
       │ Conversation│   │ Deterministic│   │ Events →     │
       │ Manager    │    │ Questions   │    │ Features     │
       │ Safety     │    └─────────────┘    └──────┬───────┘
       │ Text       │                               │
       │ Voice      │                               │
       └──────┬─────┘                               │
              │                                     │
              └────────────────┬────────────────────┘
                               ▼
                    ┌───────────────────────┐
                    │     MEDHA V2          │
                    │      ADAPTER          │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    FROZEN V2 ENGINE   │
                    │                       │
                    │ Structured            │
                    │ Text                  │
                    │ Voice                 │
                    │ Behaviour             │
                    │ Fusion                │
                    │ GRU                   │
                    │ Triage                │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      PostgreSQL       │
                    │                       │
                    │ Users                 │
                    │ Therapists            │
                    │ Cases                 │
                    │ Sessions              │
                    │ Messages              │
                    │ Check-ins             │
                    │ Questions             │
                    │ Answers               │
                    │ Observations          │
                    │ Structured Features   │
                    │ Behaviour Events      │
                    │ Behaviour Features    │
                    │ Voice                 │
                    │ Journal               │
                    │ Predictions           │
                    │ Safety Events         │
                    │ Audit Logs            │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ THERAPIST DASHBOARD   │
                    │                       │
                    │ Users                 │
                    │ Current DDS           │
                    │ Future Risk           │
                    │ Triage                │
                    │ History               │
                    │ Behaviour             │
                    │ Check-ins             │
                    │ Alerts                │
                    └───────────────────────┘

---

# 23. Implementation Sequence Summary

The team should execute the prompts in this exact order:

1. Repository Audit
2. FastAPI Foundation
3. PostgreSQL/SQLAlchemy/Alembic
4. User/Therapist Models
5. Authentication
6. RBAC
7. Therapist Creates Users
8. Case Management
9. Persistent Sessions
10. Chatbot Integration
11. Safety Integration
12. Question Engine Integration
13. Check-in Persistence
14. Structured Features
15. Event Ingestion
16. Behaviour Aggregator
17. Voice
18. Journal
19. V2 Adapter
20. Prediction Service
21. Triage
22. Therapist Prediction APIs
23. Therapist Behaviour/Check-in APIs
24. Therapist Alerts
25. Insights
26. Notifications
27. Authorization Audit
28. Privacy Audit
29. Audit Logging
30. End-to-End User Flow
31. Security Integration Tests
32. Behaviour/V2 Integration Tests
33. Production Configuration
34. Migration Verification
35. Final Backend Audit

---

# 24. Final Rule

The backend exists to connect the MEDHA application to the intelligence that already exists.

It is NOT a second ML system.

It is NOT a second Question Engine.

It is NOT a replacement for ConversationManager.

It is NOT a modification of MEDHA V2.

Its responsibilities are:

AUTHENTICATE
AUTHORIZE
PERSIST
ORCHESTRATE
INTEGRATE
PROTECT
SERVE

The final product is:

User App
    ↓
MEDHA Backend
    ↓
Existing MEDHA Chatbot + Question Engine + Safety + V2
    ↓
Persistent MEDHA Data
    ↓
Therapist Dashboard