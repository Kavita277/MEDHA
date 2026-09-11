# Step 31 — Security Integration Tests Summary

## Overview

Step 31 implements a comprehensive, end-to-end security integration test suite for the MEDHA Backend in adherence to `backend_plan.md §31`. The suite validates all 10 core security requirements across authentication, role-based access control (RBAC), multi-tenant case isolation, runtime account status enforcement, credential confidentiality, and patient-facing privacy boundaries.

---

## The 10 Security Requirements & Test Coverage

### 1. User Cannot Access Therapist Dashboard
- **Requirement**: Users holding the `USER` role must never be permitted to access therapist-only dashboard routes or mutate clinical data.
- **Endpoints Tested**:
  - `GET /api/v1/therapist/users`
  - `POST /api/v1/therapist/users`
  - `PATCH /api/v1/therapist/users/{user_id}/status`
  - `GET /api/v1/therapist/cases`
  - `PATCH /api/v1/therapist/cases/{case_id}`
  - `GET /api/v1/therapist/cases/{case_id}/results`
  - `GET /api/v1/therapist/cases/{case_id}/sessions`
  - `GET /api/v1/therapist/cases/{case_id}/checkins`
  - `GET /api/v1/therapist/cases/{case_id}/behaviour`
  - `GET /api/v1/therapist/cases/{case_id}/alerts`
  - `PATCH /api/v1/therapist/cases/{case_id}/alerts/{alert_id}`
  - `GET /api/v1/therapist/cases/{case_id}/insights`
  - `GET /api/v1/therapist/cases/{case_id}/recommendations`
  - `GET /api/v1/therapist/cases/{case_id}/safety-protocol`
  - `GET /api/v1/therapist/sessions/{session_id}/results`
  - `GET /api/v1/therapist/sessions/{session_id}/insights`
  - `GET /api/v1/therapist/sessions/{session_id}/recommendations`
  - `GET /api/v1/therapist/sessions/{session_id}/safety-protocol`
  - `GET /api/v1/therapist/audit-logs`
- **Expected Authorization Behavior**: Every route rejects the request with **HTTP 403 Forbidden** and a descriptive error message (`"Insufficient permissions. Required role: therapist."`).

### 2. User Cannot Access Predictions
- **Requirement**: Prediction results, specialist model scores, triage classifications, and risk trajectories are strictly therapist-only and must never be exposed to users.
- **Endpoints Tested**:
  - `GET /api/v1/therapist/cases/{case_id}/results`
  - `GET /api/v1/therapist/sessions/{session_id}/results`
- **Expected Authorization Behavior**: HTTP 403 Forbidden. Response payload never contains prediction models, `fusion_dds_prediction`, or specialist scores.

### 3. User Cannot Access Another User's Data
- **Requirement**: Strict cross-patient isolation. Patient A must never be able to inspect, participate in, or alter Patient B's clinical resources.
- **Endpoints Tested**:
  - `GET /api/v1/sessions/{user_b_session_id}` $\rightarrow$ **HTTP 403 Forbidden** (`"Access denied. You may only access sessions belonging to your own case."`)
  - `POST /api/v1/sessions/{user_b_session_id}/end` $\rightarrow$ **HTTP 403 Forbidden**
  - `GET /api/v1/chat/sessions/{user_b_session_id}/history` $\rightarrow$ **HTTP 403 Forbidden** (Confidential messages from Patient B are never leaked)
  - `POST /api/v1/chat/sessions/{user_b_session_id}/message` $\rightarrow$ **HTTP 403 Forbidden**
  - `GET /api/v1/checkins/{user_b_checkin_id}` $\rightarrow$ **HTTP 403 Forbidden**
  - `POST /api/v1/checkins/{user_b_checkin_id}/answer` $\rightarrow$ **HTTP 403 Forbidden**
  - `GET /api/v1/journal/{user_b_journal_id}` $\rightarrow$ **HTTP 404 Not Found** (anti-enumeration: filtered strictly by requesting patient's case)
  - `PATCH /api/v1/journal/{user_b_journal_id}` $\rightarrow$ **HTTP 404 Not Found**
- **Expected Authorization Behavior**: 403 Forbidden on session/chat/check-in operations; 404 Not Found anti-enumeration on journal queries.

### 4. Therapist Cannot Access Another Therapist's Case
- **Requirement**: Multi-tenant therapist isolation. Therapist B must not be able to view, list, update, or handle alerts for cases assigned to Therapist A.
- **Endpoints Tested**:
  - `GET /api/v1/therapist/cases` (Therapist B's listing excludes Case A)
  - `PATCH /api/v1/therapist/cases/{case_id}`
  - `GET /api/v1/therapist/cases/{case_id}/results`
  - `GET /api/v1/therapist/cases/{case_id}/sessions`
  - `GET /api/v1/therapist/cases/{case_id}/checkins`
  - `GET /api/v1/therapist/cases/{case_id}/behaviour`
  - `GET /api/v1/therapist/cases/{case_id}/alerts`
  - `PATCH /api/v1/therapist/cases/{case_id}/alerts/{alert_id}`
  - `GET /api/v1/therapist/cases/{case_id}/insights`
  - `GET /api/v1/therapist/cases/{case_id}/recommendations`
  - `GET /api/v1/therapist/cases/{case_id}/safety-protocol`
  - `GET /api/v1/therapist/sessions/{session_id}/results`
  - `GET /api/v1/therapist/sessions/{session_id}/insights`
  - `GET /api/v1/therapist/sessions/{session_id}/recommendations`
  - `GET /api/v1/therapist/sessions/{session_id}/safety-protocol`
- **Expected Authorization Behavior**: **HTTP 403 Forbidden** with anti-enumeration (`"Case not found or access denied."`), preventing foreign therapists from determining whether an unassigned case exists.

### 5. Therapist Can Access Assigned Case
- **Requirement**: Positive access verification. The assigned therapist has seamless access to clinical data for their cases.
- **Endpoints Tested**:
  - `GET /api/v1/therapist/cases` $\rightarrow$ Case A present
  - `GET /api/v1/therapist/cases/{case_id}/results` $\rightarrow$ **HTTP 200 OK** (`results_available=True`, `fusion_dds_prediction=52.5`)
  - `GET /api/v1/therapist/cases/{case_id}/sessions` $\rightarrow$ **HTTP 200 OK**
  - `GET /api/v1/therapist/cases/{case_id}/insights` $\rightarrow$ **HTTP 200 OK** (contains `factors` and `disclaimer`)
  - `GET /api/v1/therapist/cases/{case_id}/recommendations` $\rightarrow$ **HTTP 200 OK** (contains `recommendations`)
  - `GET /api/v1/therapist/cases/{case_id}/alerts` $\rightarrow$ **HTTP 200 OK** (contains active alerts with `severity="HIGH"`)

### 6. Invalid JWT Rejected
- **Requirement**: Malformed, random, empty, or signature-tampered tokens must be rejected.
- **Vectors Tested**:
  - `not.a.valid.jwt`
  - `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsig`
  - `random_garbage_string_12345!@#$`
  - Empty string `""`
  - Tampered signature token
  - Missing `"Bearer "` prefix
- **Expected Authorization Behavior**: **HTTP 401 Unauthorized** across both user and therapist routes.

### 7. Expired JWT Rejected
- **Requirement**: Tokens whose expiration claim `exp` is in the past must be rejected.
- **Vectors Tested**:
  - Expired user token (`expires_delta = timedelta(hours=-1)`) against `/api/v1/auth/me`
  - Expired therapist token (`expires_delta = timedelta(minutes=-30)`) against `/api/v1/therapist/cases`
- **Expected Authorization Behavior**: **HTTP 401 Unauthorized** (`"Could not validate credentials or token expired"`).

### 8. Suspended / Deactivated Account Rejected
- **Requirement**: Runtime status check must invalidate access for inactive accounts, even if the client presents a cryptographically valid, unexpired token.
- **Vectors Tested**:
  - Active user transitions to `UserStatus.SUSPENDED` $\rightarrow$ `/auth/me` and `/sessions` return **HTTP 403 Forbidden** (`"Account access denied. Account status is suspended."`)
  - Active user transitions to `UserStatus.DEACTIVATED` $\rightarrow$ `/auth/me` returns **HTTP 403 Forbidden** (`"Account access denied. Account status is deactivated."`)
  - Active therapist transitions to `UserStatus.SUSPENDED` $\rightarrow$ `/therapist/cases` returns **HTTP 403 Forbidden** (`"Account access denied. Account status is suspended."`)
  - Safe state restoration restores account back to `ACTIVE` after verification.

### 9. Password Is Never Returned
- **Requirement**: Sensitive credential fields must never be serialized or leaked in HTTP responses.
- **Endpoints Tested**:
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
  - `POST /api/v1/therapist/users` (Provision patient)
  - `GET /api/v1/therapist/cases`
  - `GET /api/v1/therapist/audit-logs`
- **Verification Method**: Recursive search across all JSON keys and raw text bodies. Asserted that none of `password`, `password_hash`, `hashed_password`, `raw_password`, or `user_password` are returned.

### 10. Prediction Data Is Never Returned by USER Endpoints
- **Requirement**: Patient-facing endpoints must maintain strict clinical boundary isolation and never expose prediction or risk metrics.
- **Endpoints Tested**:
  - `POST /api/v1/sessions` (Create session)
  - `GET /api/v1/sessions/{id}` (Get session detail)
  - `GET /api/v1/chat/sessions/{id}/history` (Chat history)
  - `GET /api/v1/checkins/{id}` (Check-in state)
  - `GET /api/v1/journal` (List journal entries)
  - `POST /api/v1/journal` (Create journal entry)
- **Verification Method**: Recursive key search asserting absence of:
  - `fusion_dds_prediction`
  - `temporal_risk_score`
  - `future_escalation_flag`
  - `triage_level`
  - `struct_pred`
  - `text_pred`
  - `voice_pred`
  - `behav_pred`
  - `specialists`

---

## Anti-Enumeration & Information Leakage Prevention

The MEDHA backend implements deliberate anti-enumeration security controls verified in this test suite:
1. **Case ID Anti-Enumeration**:
   When a therapist queries `/api/v1/therapist/cases/{case_id}/*` for a non-existent case or a case assigned to a different therapist, the backend always responds with `403 Forbidden` (`detail="Case not found or access denied."`). This prevents attackers from scanning UUIDs to determine which cases exist in the system.
2. **Patient Journal Scoping**:
   Journal queries (`/api/v1/journal/{entry_id}`) are automatically scoped to the active case of the authenticated user. A request for another user's entry returns `404 Not Found` rather than `403`, preventing attackers from enumerating journal entry IDs.
3. **Session Verification**:
   Session access is validated through the complete chain `session -> case -> user_id / therapist_id`, preventing unauthorized session identifier guessing.

---

## Verification Results

### Focused Test Suite (`test_step31_security_integration.py`)
```
python -m pytest backend/tests/test_step31_security_integration.py -v
================== 70 passed, 2 warnings in 115.50s (0:01:55) ==================
```

### Complete Backend Test Suite
```
python -m pytest backend/tests -v
================== 258 passed, 34 warnings in ~400s ==================
```
*(Baseline: 188 passed $\rightarrow$ 258 passed, 0 failed, 0 errors)*

---

## Confirmation of Invariants
- **Production Code**: Zero modifications to application or production code.
- **Existing Tests**: Zero existing tests modified.
- **Alembic Migrations**: Zero database migrations created.
- **ML Engines & Models**: Zero changes to frozen V2 models, artifacts, or weights.
