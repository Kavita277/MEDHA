# MEDHA Backend Data Privacy Audit (Step 28)

## 1. Executive Summary

This document reports the comprehensive findings and privacy hardening measures implemented in accordance with **MEDHA Backend Plan §28 (Data Privacy Audit)**.

The objective of the audit is to ensure absolute clinical and cryptographic confidentiality across all API surfaces, background queues, persistence models, logs, exception handlers, and client responses.

---

## 2. Comprehensive Audit Matrix of Sensitive Data Categories

| Sensitive Category | Target Constraint | Backend Audit Result & Protection Mechanism | Status |
| :--- | :--- | :--- | :--- |
| **DDS (Distress & Depression Score)** | Never exposed to patient/user endpoints | Fused DDS score (`fusion_dds_prediction`) is strictly confined to therapist-only schemas (`CaseResultResponse`, `CaseRecommendationsResponse`). Patient response models (`SessionResponse`, `CheckInResponse`, `ChatTurnResult`, `VoiceCheckInResponse`) contain zero DDS fields. | **VERIFIED / ISOLATED** |
| **Future Risk & Escalation Flags** | Never exposed to patient/user endpoints | `future_escalation_flag` and `temporal_risk_score` are strictly confined to therapist-only results endpoints protected by 3-Layer RBAC (`get_current_therapist` + case ownership). | **VERIFIED / ISOLATED** |
| **Model Reasoning & Specialist Internals** | Never exposed to patients; no raw internal weights | Specialist probabilities (`struct_pred`, `text_pred`, `voice_pred`, `behav_pred`) are therapist-only. Therapist decision-support APIs present human-in-the-loop clinical recommendations and non-diagnostic summaries without exposing raw model weights or mathematical heuristics. | **VERIFIED / ISOLATED** |
| **Safety Internals & Rule Triggers** | Patient receives non-alarming safety responses; clinician receives decision support | In patient chat turns, `ChatTurnResult` returns boolean `safety_triggered` only (for client-side supportive UI rendering); safety rule IDs, threshold formulas, and internal trigger categories remain encapsulated on the backend. Clinicians access structured protocol guidance via `/safety-protocol`. | **VERIFIED / ISOLATED** |
| **Password Hashes & Salt Secrets** | Never exposed in any API response or log | `password_hash` is marked non-serializable in Pydantic domain models; `UserResponse` explicitly omits `password_hash`. `sanitize_payload()` scrubs any dictionary key matching `password*` or `*hash*`. | **VERIFIED / REDACTED** |
| **API Keys & JWT Tokens** | Never logged or reflected in errors/audits | `_JWT_BEARER_PATTERN` regex automatically scrubs any string starting with `Bearer ` or matching JWT structure (`eyJ...`) from logs, validation error bodies, and audit metadata payloads. Query parameters named `token`, `secret`, `jwt`, `api_key` are scrubbed before access logging. | **VERIFIED / REDACTED** |
| **Raw Voice / Audio Data** | Raw audio is never persisted in DB or logs; temporary files securely purged | Uploaded audio check-in files are streamed to temporary OS files, processed via `MedhaVoiceAdapter`, and **immediately deleted in `finally:` blocks**. Only derived acoustic metadata and availability flags are persisted in `voice_records`. | **VERIFIED / PURGED** |
| **Chat & Journal Transcripts** | Isolated by patient ID and case assignment; excluded from audit metadata | Patient chat history (`/chat/sessions/{id}/history`) and journal entries (`/journal`) enforce strict case ownership. Audit logging records event occurrence (`action="THERAPIST_VIEWED_INSIGHTS"`, `action="USER_LOGIN"`) without copying message text or journal transcripts into `audit_logs`. | **VERIFIED / ISOLATED** |
| **Unauthorized User Data (Cross-Patient / Cross-Therapist)** | Strict 3-Layer RBAC and anti-enumeration | Patients receive HTTP 403 on therapist endpoints. Foreign therapists attempting to access unassigned cases receive HTTP 403 (`"Case not found or access denied."`) rather than 404, eliminating identifier enumeration vulnerabilities. | **VERIFIED / HARDENED** |

---

## 3. Patient vs. Therapist Endpoint Separation Audit

### Patient (`USER` Role) Endpoints:
- `POST /api/v1/auth/login` → Returns JWT and `UserResponse` (no password hash).
- `GET /api/v1/auth/me` → Returns `UserResponse` (id, email, name, role, status; no secrets).
- `POST /api/v1/sessions` → Returns `SessionResponse` (session identifier, timepoint, status, turn count; no DDS or risk scores).
- `GET /api/v1/sessions/{id}` → Returns `SessionResponse` with ownership check.
- `POST /api/v1/chat/sessions/{id}/message` → Returns `ChatTurnResult` (turn index, sanitized assistant response, boolean `safety_triggered`).
- `GET /api/v1/chat/sessions/{id}/history` → Returns `ChatHistoryResponse` (messages for the authenticated user's session only).
- `POST /api/v1/checkins/sessions/{id}` → Returns `CheckInResponse` (current question text/type; no feature vectors).
- `POST /api/v1/checkins/{id}/answer` → Returns `CheckInAnswerResponse` (next question or completion state).
- `POST /api/v1/voice/checkin` → Returns `VoiceCheckInResponse` (record ID, timepoint, availability flag; no raw audio or ML predictions).
- `GET/POST/PATCH /api/v1/journal` → Returns `JournalEntryResponse` (scoped to user's active case).
- `POST /api/v1/events/batch` → Ingests behavioral telemetry idempotently with case ownership verification.

### Therapist (`THERAPIST` Role) Decision-Support Endpoints:
- `GET /api/v1/therapist/users` → Lists assigned patients with case metadata.
- `GET /api/v1/therapist/cases/{case_id}/results` → Latest prediction results and specialist availability.
- `GET /api/v1/therapist/cases/{case_id}/insights` → Factor breakdowns and clinical trend explainability.
- `GET /api/v1/therapist/cases/{case_id}/recommendations` → Clinical decision-support interventions and resources.
- `GET /api/v1/therapist/cases/{case_id}/safety-protocol` → Evaluated dynamic safety alerts and CTAs.
- `GET /api/v1/therapist/audit-logs` → Clinician-specific compliance audit trail.

---

## 4. Application Logging & Exception Handling Protections

1. **Validation Error Sanitization (`backend/security/redaction.py:sanitize_validation_errors`)**:
   - Pydantic 422 `RequestValidationError` responses preserve structural validation errors (`loc`, `msg`, `type`), but automatically redact the `input` value whenever a sensitive field (e.g. `password`, `token`, `secret`) fails validation.
   - Raw user credentials are never logged or reflected back to clients.

2. **Access Log Query Redaction (`backend/main.py:log_request_timing`)**:
   - Middleware scrubs query parameters containing sensitive keys before writing request lines to stdout.

3. **Internal Error Masking (`backend/security/redaction.py:mask_internal_error`)**:
   - Internal filesystem paths (`C:\...`, `/home/...`), Python memory addresses, and engine tracebacks are stripped from HTTP exception responses.
   - External clients receive structured, safe error messages (`"Internal server error occurred."`, `"Voice processing failed."`, `"Conversation processing failed."`).

4. **Audit Metadata Firewall (`backend/services/audit_service.py`)**:
   - Delegates all metadata sanitization to the centralized `sanitize_payload()` engine.

---

## 5. Conclusion & Verification

All backend components comply with the MEDHA Data Privacy specification:
- **0 ML Engine modifications** were performed.
- **100% of Patient endpoints** are devoid of raw DDS, temporal risk, specialist outputs, and diagnostic predictions.
- **100% of credentials, tokens, and raw audio files** are shielded from logs, error messages, and persistent storage.
