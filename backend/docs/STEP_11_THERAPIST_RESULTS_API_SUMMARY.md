# STEP 11: THERAPIST RESULTS API — IMPLEMENTATION SUMMARY

## 1. Objective

Step 11 builds the secure, therapist-facing Results API layer for MEDHA. It exposes
frozen V2 prediction results through a role-enforced REST API, enabling the therapist
dashboard to display prediction outcomes, triage levels, and specialist results.

The API is designed so that a future PredictionService can populate the `prediction_results`
table without altering any authorization logic.

---

## 2. Endpoints Implemented

All endpoints are served under `/api/v1/`. Step 10 (Frozen V2 Behaviour Specialist)
remains intentionally BLOCKED.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/therapist/cases` | List all cases belonging to the authenticated therapist |
| `GET` | `/api/v1/therapist/cases/{case_id}/results` | Latest MEDHA prediction for a case |
| `GET` | `/api/v1/therapist/cases/{case_id}/sessions` | All sessions for a therapist-owned case |
| `GET` | `/api/v1/therapist/sessions/{session_id}/results` | Latest prediction for a specific session |

All endpoints require `Authorization: Bearer <JWT>` with the therapist role.

---

## 3. Request / Response Schemas

### `GET /api/v1/therapist/cases` → `List[CaseSummaryResponse]`

```json
[
  {
    "case_id": "uuid",
    "victim_id": "V-P1-001",
    "user_id": "uuid",
    "status": "active",
    "current_timepoint": 3,
    "patient_name": "Patient One",
    "patient_email": "p1@medha.test",
    "case_created_at": "2026-09-10T..."
  }
]
```

### `GET /api/v1/therapist/cases/{case_id}/results` → `CaseResultResponse`

**No prediction yet (results_available = False):**
```json
{
  "case_id": "uuid",
  "victim_id": "V-P2-001",
  "user_id": "uuid",
  "results_available": false,
  "fusion_dds_prediction": null,
  "temporal_risk_score": null,
  "future_escalation_flag": null,
  "triage_level": "UNKNOWN",
  "specialists": {
    "struct_pred": null, "text_pred": null, "voice_pred": null, "behav_pred": null,
    "struct_available": false, "text_available": false, "voice_available": false, "behav_available": false,
    "behav_blocked": true,
    "behav_block_reason": "Frozen V2 Behaviour Specialist integration is blocked..."
  },
  "predicted_at": null,
  "result_record_created_at": null
}
```

**With prediction (results_available = True):**
```json
{
  "case_id": "uuid",
  "victim_id": "V-P1-001",
  "results_available": true,
  "fusion_dds_prediction": 67.4,
  "temporal_risk_score": 0.72,
  "future_escalation_flag": 1,
  "triage_level": "HIGH",
  "specialists": {
    "struct_pred": 65.2, "text_pred": 70.1, "voice_pred": null, "behav_pred": null,
    "struct_available": true, "text_available": true, "voice_available": false, "behav_available": false,
    "behav_blocked": true,
    "behav_block_reason": "..."
  },
  "predicted_at": "2026-09-10T18:00:00Z",
  "result_record_created_at": "2026-09-10T18:00:01Z"
}
```

### `GET /api/v1/therapist/cases/{case_id}/sessions` → `List[SessionSummaryResponse]`

```json
[
  {
    "session_id": "uuid",
    "session_identifier": "sess_p1_001",
    "timepoint": 3,
    "status": "ENDED",
    "closed_at": "2026-09-10T...",
    "created_at": "2026-09-10T..."
  }
]
```

---

## 4. Authorization Model

### Chain Verification

```
JWT Token
  ↓ (401 if missing/expired)
User.role == THERAPIST
  ↓ (403 if USER role)
Therapist profile linked
  ↓ (403 if no Therapist record)
Case.therapist_id == current_therapist.id
  ↓ (403 if case doesn't exist OR belongs to another therapist)
Session.case_id == authorized_case.id
  ↓ (403 if session doesn't belong to case)
PredictionResultModel for that case/session
```

### Information Leakage Prevention

When a case belongs to another therapist, the response is HTTP **403** (not 404).
This prevents enumeration attacks from distinguishing "does not exist" from
"forbidden". The same applies to sessions.

Patients (USER role) receive 403 at the THERAPIST role check — they cannot
reach any of these endpoints.

### What is NOT exposed

- `password_hash`, JWT secrets
- Model file paths, model weights, scaler internals
- Internal Python class details (`V2PredictionResult`, `MedhaState`)
- Other therapists' patients or cases
- Raw database PKs for unrelated entities

---

## 5. Case Ownership Rules

- Every case has a `therapist_id` FK.
- `CaseRepository.list_cases_for_therapist(therapist_id)` is the authoritative
  isolation query — it only returns cases where `Case.therapist_id` matches.
- `_get_authorized_case()` helper in `therapist_results.py` performs the
  ownership check for single-case lookups.

---

## 6. Session Ownership Rules

Sessions are verified through their parent case:

```
GET /therapist/sessions/{session_id}/results
  1. Session exists (else 403)
  2. Case for session exists (else 403)
  3. Case.therapist_id == requesting therapist (else 403)
```

Authorization is never based on `session_id` alone.

---

## 7. Missing Prediction Semantics

**MISSING ≠ ZERO.** This is a core MEDHA invariant.

| Scenario | `results_available` | All prediction fields |
|----------|---------------------|-----------------------|
| No prediction record exists | `false` | `null` |
| Prediction exists, voice unavailable | `true` | `voice_pred = null` |
| Step 10 blocked | (any) | `behav_pred = null` always |

The API returns HTTP **200** even when `results_available = false`. This is
not an error state; it is the normal state for a case that has not been scored yet.

---

## 8. Triage Handling

Triage is computed by a single centralized service:
[`backend/services/triage_service.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/services/triage_service.py)

**Thresholds (exact match to MEDHA_V2_ARCHITECTURE.md §6):**

| Level | Condition |
|-------|-----------|
| CRITICAL | DDS ≥ 75 OR risk ≥ 0.85 |
| HIGH | DDS ≥ 50 OR risk ≥ 0.50 |
| MEDIUM | DDS ≥ 25 OR risk ≥ 0.25 |
| LOW | DDS < 25 AND risk < 0.25 |
| UNKNOWN | Both DDS and risk unavailable (null) |

Triage is stored on the `PredictionResultModel` for auditability. If the stored
value is absent, the API computes it at read-time using `compute_triage_level()`.
Thresholds are **never duplicated** — `triage_service.py` is the single source.

---

## 9. Persistence Model

### `PredictionResultModel` (table: `prediction_results`)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | PK |
| `case_id` | UUID FK→cases | No | Ownership chain |
| `session_id` | UUID FK→chat_sessions | Yes | Optional; case-level results have null |
| `timepoint` | Integer | No | Timepoint at prediction |
| `fusion_dds_prediction` | Float | Yes | Null = unavailable |
| `temporal_risk_score` | Float | Yes | Null = GRU unavailable |
| `future_escalation_flag` | Integer | Yes | 1/0/null |
| `triage_level` | String(16) | Yes | CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN |
| `struct_pred` | Float | Yes | Null = unavailable |
| `text_pred` | Float | Yes | Null = unavailable |
| `voice_pred` | Float | Yes | Null = unavailable |
| `behav_pred` | Float | Yes | **Always null (Step 10 blocked)** |
| `struct_available` | Boolean | No | |
| `text_available` | Boolean | No | |
| `voice_available` | Boolean | No | |
| `behav_available` | Boolean | No | **Always False (Step 10 blocked)** |
| `predicted_at` | DateTime TZ | No | When prediction was generated |
| `created_at` | DateTime TZ | No | |
| `updated_at` | DateTime TZ | No | |

Migration: `b3f7e291cc4a_add_prediction_results_table.py` (chains from `ead3432ccad1`).

---

## 10. Privacy / Data Minimization

- `GET /therapist/cases` returns only: `case_id`, `victim_id`, `user_id`, `status`,
  `current_timepoint`, `patient_name`, `patient_email`, `case_created_at`.
- No `password_hash`, no raw database row dumps, no model internals.
- Patient emails are included because they are needed for dashboard identification.
- `GET /therapist/cases/{id}/results` returns clinical signals only;
  no model weights, file paths, or scaler info is serialized.

---

## 11. Test Coverage

File: [`backend/tests/test_therapist_results_api.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_therapist_results_api.py)

**28 tests, all passed.**

| ID | Test | Result |
|----|------|--------|
| A | Therapist can list own cases | ✅ PASS |
| B | Therapist cannot list another therapist's cases | ✅ PASS |
| C | Therapist can retrieve results for own case | ✅ PASS |
| D | Therapist cannot retrieve another therapist's case results | ✅ PASS |
| E | Therapist can retrieve session list for own case | ✅ PASS |
| F | Therapist cannot retrieve another therapist's session list | ✅ PASS |
| G | Patient cannot access therapist results endpoints (all 4) | ✅ PASS |
| H | Unauthenticated user receives 401 on all 4 endpoints | ✅ PASS |
| I | Case with no prediction returns null fields (not zeros) | ✅ PASS |
| J | Missing specialist prediction (voice) is null | ✅ PASS |
| K | Existing predictions returned correctly | ✅ PASS |
| L | Triage returned correctly (HIGH); UNKNOWN when no prediction | ✅ PASS |
| M | Session from different case cannot bypass authorization | ✅ PASS |
| N | Prediction from other case not accessible by ID manipulation | ✅ PASS |
| O | Case list response shape is correct (no password fields) | ✅ PASS |
| P | `behav_pred` always null (Step 10 blocked) | ✅ PASS |
| Q | `behav_blocked` always True | ✅ PASS |
| R | `results_available` flag semantics correct | ✅ PASS |
| S | Therapist can get own session results correctly | ✅ PASS |
| T | Wrong therapist cannot get session results | ✅ PASS |
| — | TriageService unit tests (7 cases) | ✅ PASS |

**Regression: 74 existing tests — all passed (0 failures).**

---

## 12. What Remains Blocked

> **Frozen V2 Behaviour Specialist integration remains intentionally blocked because
> the original generator for `Engagement_Score` and dependent features
> (`Baseline_Engagement`, `Engagement_Deviation`, `Behaviour_Trend`) was not
> recovered (see STEP_9C_ORIGINAL_V2_GENERATOR_RECOVERY.md).**

- `behav_pred` is always `null`
- `behav_available` is always `false`
- `behav_blocked = true` is explicitly surfaced in every response
- `behav_block_reason` explains the blocker to API consumers

The API design ensures this can be resolved without touching the authorization layer.

---

## 13. Future PredictionService Integration

The API layer is intentionally decoupled from prediction computation:

```
PredictionService (future)
  ↓ runs inference
  ↓ calls PredictionResultRepository.create(PredictionResultModel(...))
  
Therapist Results API (this step)
  ↓ GET request
  ↓ authorization check (unchanged)
  ↓ PredictionResultRepository.get_latest_for_case(case_id)
  ↓ returns result
```

**To integrate a PredictionService:**
1. Compute DDS, temporal risk, triage via the existing frozen V2 pipeline.
2. Create a `PredictionResultModel` record and persist via `PredictionResultRepository`.
3. The Therapist Results API automatically serves it without modification.

**To unblock Step 10 (Behaviour Specialist):**
1. Implement `behav_pred` computation in the PredictionService.
2. Set `behav_pred` and `behav_available=True` when persisting the result.
3. Update `behav_blocked=False` and `behav_block_reason` in `therapist_results.py`.
4. No schema changes required.

---

## 14. Files Created / Modified

### Created
| File | Description |
|------|-------------|
| [`backend/persistence/models/prediction_result.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/prediction_result.py) | ORM model |
| [`backend/persistence/repositories/prediction_result.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/prediction_result.py) | Data access layer |
| [`backend/services/triage_service.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/services/triage_service.py) | Centralized triage logic |
| [`backend/schemas/results.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/results.py) | Pydantic response schemas |
| [`backend/api/v1/endpoints/therapist_results.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/api/v1/endpoints/therapist_results.py) | 4 therapist result endpoints |
| [`backend/persistence/migrations/versions/b3f7e291cc4a_add_prediction_results_table.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/migrations/versions/b3f7e291cc4a_add_prediction_results_table.py) | Alembic migration |
| [`backend/tests/test_therapist_results_api.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_therapist_results_api.py) | 28 tests |

### Modified
| File | Change |
|------|--------|
| [`backend/persistence/models/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/__init__.py) | Exports `PredictionResultModel` |
| [`backend/persistence/repositories/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/__init__.py) | Exports `PredictionResultRepository` |
| [`backend/api/v1/router.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/api/v1/router.py) | Registers `therapist_results` router |
