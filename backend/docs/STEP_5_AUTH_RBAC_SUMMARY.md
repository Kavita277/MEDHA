# MEDHA Backend — Step 5: Authentication & RBAC Summary

## 1. Overview & Objectives

In this step, the Authentication and Role-Based Access Control (RBAC) foundation was implemented for the MEDHA MVP Backend. 

The primary objectives achieved include:
1. Secure password hashing with `bcrypt` (never storing or leaking plaintext passwords).
2. JWT-based authentication with `pyjwt` and claim validation (`sub`, `role`, `iat`, `exp`, `jti`).
3. Current authenticated user dependency with active status validation (`ACTIVE` required, `SUSPENDED` and `DEACTIVATED` accounts rejected with HTTP 403 Forbidden).
4. Role enforcement dependencies (`require_role`, `get_current_therapist`, `get_current_patient`).
5. `Case` database model and repository linking patient `User` accounts to assigned clinicians (`Therapist`), preserving longitudinal `victim_id` for frozen MEDHA V2 compatibility.
6. Public and clinician-facing API endpoints:
   - `POST /api/v1/auth/login`
   - `GET /api/v1/auth/me`
   - `POST /api/v1/therapist/users`
   - `GET /api/v1/therapist/users`
7. Strict data isolation: Clinicians can only access and view patients assigned to their own cases.
8. Zero modifications to `chatbot/`, `engine/`, or frozen ML weights/pipelines.

---

## 2. Files Created and Modified

### Created Files
| File Path | Description |
| :--- | :--- |
| [`backend/security/passwords.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/security/passwords.py) | Cryptographic password hashing and verification using `bcrypt`. |
| [`backend/security/tokens.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/security/tokens.py) | JWT token creation, signing, claims embedding, and verification using `pyjwt`. |
| [`backend/security/dependencies.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/security/dependencies.py) | FastAPI dependency providers (`get_current_user`, `require_role`, `get_current_therapist`, `get_current_patient`). |
| [`backend/persistence/models/case.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/case.py) | SQLAlchemy 2.0 `Case` model linking `User` and `Therapist` with `victim_id`. |
| [`backend/persistence/repositories/case.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/case.py) | Case data access methods and multi-tenant patient roster queries. |
| [`backend/persistence/migrations/versions/002_create_cases.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/migrations/versions/002_create_cases.py) | Alembic migration for creating the `cases` table. |
| [`backend/schemas/auth.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/auth.py) | Pydantic schemas for `LoginRequest` and `TokenResponse`. |
| [`backend/schemas/case.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/case.py) | Pydantic schemas for `CaseResponse`, `TherapistCreateUserRequest`, and `TherapistUserResponse`. |
| [`backend/api/v1/endpoints/auth.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/api/v1/endpoints/auth.py) | Endpoint handlers for `POST /api/v1/auth/login` and `GET /api/v1/auth/me`. |
| [`backend/api/v1/endpoints/therapist.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/api/v1/endpoints/therapist.py) | Endpoint handlers for `POST /api/v1/therapist/users` and `GET /api/v1/therapist/users`. |
| [`backend/tests/test_security_utils.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_security_utils.py) | Unit tests for bcrypt hashing and JWT token expiration/decoding. |
| [`backend/tests/test_auth_api.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_auth_api.py) | Functional tests for login, token issuance, status enforcement, and `/me`. |
| [`backend/tests/test_therapist_api.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_therapist_api.py) | Functional tests for patient creation, auto victim ID, duplicate checks, RBAC 403, and strict data isolation. |
| [`backend/tests/test_case_models.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_case_models.py) | Unit tests for `Case` model persistence, relationships, and queries. |
| [`backend/docs/STEP_5_AUTH_RBAC_SUMMARY.md`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/docs/STEP_5_AUTH_RBAC_SUMMARY.md) | This complete summary document. |

### Modified Files
| File Path | Changes Made |
| :--- | :--- |
| [`requirements.txt`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/requirements.txt) | Added `bcrypt>=4.0.0` and `pyjwt>=2.8.0`. |
| [`backend/config.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/config.py) | Added `JWT_SECRET_KEY`, `JWT_ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES`. |
| [`backend/security/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/security/__init__.py) | Exported password, token, and dependency utilities. |
| [`backend/persistence/models/user.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/user.py) | Added bidirectional `cases` relationship. |
| [`backend/persistence/models/therapist.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/therapist.py) | Added bidirectional `cases` relationship. |
| [`backend/persistence/models/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/__init__.py) | Exported `Case` model. |
| [`backend/persistence/repositories/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/__init__.py) | Exported `CaseRepository` and added `.create()` alias in `BaseRepository`. |
| [`backend/persistence/database.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/database.py) | Enabled `StaticPool` for SQLite in-memory databases to support testing with shared session state. |
| [`backend/schemas/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/__init__.py) | Re-exported auth and case schemas. |
| [`backend/api/v1/router.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/api/v1/router.py) | Mounted `auth.router` (`/auth`) and `therapist.router` (`/therapist`). |
| [`backend/tests/test_migrations.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_migrations.py) | Added verification of migration `002_create_cases` in upgrade and downgrade passes. |

---

## 3. Implemented Endpoints & Behavioral Specifications

### 1. `POST /api/v1/auth/login`
- **Request Body**: `LoginRequest` (`email`, `password`)
- **Authentication**:
  - Normalizes email and searches in `UserRepository`.
  - Verifies password with `verify_password()`.
  - Validates account status:
    - If `SUSPENDED` or `DEACTIVATED`: Returns `403 Forbidden` with a descriptive message.
  - Updates `last_login_at` to current UTC timestamp.
  - Generates JWT Bearer access token containing user UUID, role, and email.
- **Response**: `TokenResponse` (`access_token`, `token_type`, `expires_in`, `user`).
- **Security**: The response contains serialized `UserResponse`, which excludes `password_hash`.

### 2. `GET /api/v1/auth/me`
- **Authentication**: Bearer JWT token validated via `get_current_user`.
- **Response**: `UserResponse` with account metadata and profile information.
- **Error Handling**: Missing or malformed tokens yield `401 Unauthorized`. Inactive accounts yield `403 Forbidden`.

### 3. `POST /api/v1/therapist/users`
- **Access Control**: Clinicians only (`get_current_therapist`). Regular users receive `403 Forbidden`.
- **Request Body**: `TherapistCreateUserRequest` (`name`, `email`, `password`, `mobile`, `victim_id`)
- **Provisioning Logic**:
  - Validates uniqueness of `email` and `mobile`.
  - Determines `victim_id`: Uses provided custom ID or auto-generates format `V-<HEX8>`. Validates uniqueness in `cases`.
  - Hashes password securely via `hash_password()`.
  - Creates `User` with role `USER`, status `ACTIVE`, and `must_change_password=True`.
  - Creates linked `Case` connecting the patient to the calling therapist (`therapist_id=current_therapist.id`).
- **Response**: `TherapistUserResponse` containing the created `UserResponse` and embedded `CaseResponse`.
- **Status Code**: `201 Created`.

### 4. `GET /api/v1/therapist/users`
- **Access Control**: Clinicians only (`get_current_therapist`). Regular users receive `403 Forbidden`.
- **Multi-Tenant Isolation**: Queries only cases where `therapist_id == current_therapist.id`.
  - Clinician A **never** sees Clinician B's patients or cases.
- **Response**: `List[TherapistUserResponse]` with patient profiles and active case metadata.

---

## 4. Test Verification Summary

All 49 backend unit and integration tests passed cleanly:
```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\jnark\Documents\MEDHA\MEDHA
collected 49 items

backend/tests/test_account_repositories.py ..                            [  4%]
backend/tests/test_app.py .......                                        [ 18%]
backend/tests/test_auth_api.py .........                                 [ 36%]
backend/tests/test_case_models.py ...                                    [ 42%]
backend/tests/test_database.py ........                                  [ 59%]
backend/tests/test_health.py ..                                          [ 63%]
backend/tests/test_migrations.py .                                       [ 65%]
backend/tests/test_security_utils.py ..                                  [ 69%]
backend/tests/test_therapist_api.py .......                              [ 83%]
backend/tests/test_user_models.py ........                              [100%]

======================= 49 passed, 5 warnings in 34.45s =======================
```

Regression test verification:
```
chatbot/tests/test_v2_adapter.py ..........                              [100%]
======================= 10 passed, 5 warnings in 3.54s ========================
```

---

## 5. Next Steps

With Authentication, RBAC, User models, and Case linking now in place, the system is ready for:
1. Longitudinal Check-in / Session persistence models and API endpoints.
2. Question Engine bridge & State persistence.
3. Feature Mapper & Longitudinal MEDHA V2 Adapter persistence.
