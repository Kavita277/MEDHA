# Walkthrough: Step 4 — Authentication & Account Database Models

## Summary of Accomplishments
In **STEP 4** of the MEDHA backend development plan, the core account and authentication domain models (`User` and `Therapist`) were implemented using **SQLAlchemy 2.0**, along with their corresponding **Pydantic schemas**, type-safe **repositories**, and an **Alembic migration** (`001_create_users_and_therapists.py`).

Existing `chatbot/` and `engine/` components were completely preserved without any modifications.

---

## 1. Files Created & Modified

### Models (`backend/persistence/models/`)
- [backend/persistence/models/user.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/user.py):
  - `UserRole(str, Enum)`: `USER`, `THERAPIST`.
  - `UserStatus(str, Enum)`: `ACTIVE`, `SUSPENDED`, `DEACTIVATED`.
  - `User(Base, TimestampMixin)`:
    - `id`: `Uuid(as_uuid=True)` (PK, default `uuid.uuid4`).
    - `role`: Enum with length 32, indexed, default `UserRole.USER`.
    - `name`: `String(255)`, not null.
    - `mobile`: `String(32)`, unique, indexed, nullable.
    - `email`: `String(255)`, unique, indexed, not null.
    - `password_hash`: `String(255)`, not null.
    - `status`: Enum with length 32, indexed, default `UserStatus.ACTIVE`.
    - `must_change_password`: `Boolean`, default `False`.
    - `last_login_at`: `DateTime(timezone=True)`, nullable.
    - `therapist`: 1-to-1 relationship to `Therapist` profile (`uselist=False`, `cascade="all, delete-orphan"`).
- [backend/persistence/models/therapist.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/therapist.py):
  - `Therapist(Base, TimestampMixin)`:
    - `id`: `Uuid(as_uuid=True)` (PK, default `uuid.uuid4`).
    - `user_id`: `Uuid(as_uuid=True)`, `ForeignKey("users.id", ondelete="CASCADE")`, unique, indexed.
    - `display_name`: `String(255)`, not null.
    - `user`: Relationship back to `User`.
- [backend/persistence/models/__init__.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/models/__init__.py):
  - Re-exports `User`, `UserRole`, `UserStatus`, `Therapist`, `Base`, and `TimestampMixin`.

### Schemas (`backend/schemas/`)
- [backend/schemas/user.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/user.py):
  - `UserBase`, `UserCreate`, `UserUpdate`, `UserResponse` with regex email format validation.
- [backend/schemas/therapist.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/therapist.py):
  - `TherapistBase`, `TherapistCreate`, `TherapistUpdate`, `TherapistResponse`.
- [backend/schemas/__init__.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/schemas/__init__.py):
  - Re-exports all user and therapist schemas.

### Repositories (`backend/persistence/repositories/`)
- [backend/persistence/repositories/user.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/user.py):
  - `UserRepository(BaseRepository[User])`:
    - `get_by_email(email: str)`
    - `get_by_mobile(mobile: str)`
    - `list_by_role(role: UserRole, skip, limit)`
    - `list_by_status(status: UserStatus, skip, limit)`
- [backend/persistence/repositories/therapist.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/therapist.py):
  - `TherapistRepository(BaseRepository[Therapist])`:
    - `get_by_user_id(user_id: uuid.UUID)`
    - `get_with_user(therapist_id: uuid.UUID)`
- [backend/persistence/repositories/__init__.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/repositories/__init__.py):
  - Re-exports `UserRepository` and `TherapistRepository`.

### Migrations (`backend/persistence/migrations/`)
- [backend/persistence/migrations/versions/001_create_users_and_therapists.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/migrations/versions/001_create_users_and_therapists.py):
  - Initial migration creating `users` and `therapists` tables with all constraints and indexes, and full downgrade support.
- [backend/persistence/migrations/env.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/persistence/migrations/env.py):
  - Enabled connection injection and dynamic config URL resolution.

### Tests (`backend/tests/`)
- [backend/tests/test_user_models.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_user_models.py):
  - Model creation, defaults, unique email/mobile constraints, 1-to-1 relationship, cascade delete, and Pydantic schema validation.
- [backend/tests/test_account_repositories.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_account_repositories.py):
  - CRUD operations and custom query methods on `UserRepository` and `TherapistRepository`.
- [backend/tests/test_migrations.py](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_migrations.py):
  - Programmatic execution of Alembic `upgrade head` and `downgrade base` verifying table and column creation and clean removal.

---

## 2. Verification Results

### Backend Automated Test Suite
```bash
pytest backend/tests/ -v
```
Output:
```text
backend/tests/test_account_repositories.py::test_user_repository_crud_and_lookups PASSED [  3%]
backend/tests/test_account_repositories.py::test_therapist_repository_crud_and_lookups PASSED [  7%]
backend/tests/test_app.py::test_app_startup_and_root PASSED              [ 10%]
backend/tests/test_app.py::test_api_version_routing PASSED               [ 14%]
backend/tests/test_app.py::test_not_found_error_handling PASSED          [ 17%]
backend/tests/test_cors_headers_configured PASSED           [ 21%]
backend/tests/test_process_time_header PASSED               [ 25%]
backend/tests/test_settings_configuration PASSED            [ 28%]
backend/tests/test_application_factory PASSED               [ 32%]
backend/tests/test_database.py::test_default_database_uri_generation PASSED [ 35%]
backend/tests/test_database.py::test_database_url_override_and_normalization PASSED [ 39%]
backend/tests/test_database.py::test_build_engine_sqlite PASSED          [ 42%]
backend/tests/test_database.py::test_check_db_connection PASSED          [ 46%]
backend/tests/test_database.py::test_get_db_yield_and_close PASSED       [ 50%]
backend/tests/test_database.py::test_model_timestamps PASSED             [ 53%]
backend/tests/test_database.py::test_base_repository_crud PASSED         [ 57%]
backend/tests/test_database.py::test_alembic_configuration_validity PASSED [ 60%]
backend/tests/test_health.py::test_health_endpoint PASSED                [ 64%]
backend/tests/test_health.py::test_readiness_endpoint PASSED             [ 67%]
backend/tests/test_migrations.py::test_alembic_upgrade_and_downgrade PASSED [ 71%]
backend/tests/test_user_models.py::test_create_user_defaults PASSED      [ 75%]
backend/tests/test_user_models.py::test_user_email_unique_constraint PASSED [ 78%]
backend/tests/test_user_models.py::test_user_mobile_unique_constraint PASSED [ 82%]
backend/tests/test_user_models.py::test_create_therapist_relationship PASSED [ 85%]
backend/tests/test_user_models.py::test_therapist_user_id_unique_constraint PASSED [ 89%]
backend/tests/test_user_models.py::test_cascade_delete_user_removes_therapist PASSED [ 92%]
backend/tests/test_user_models.py::test_user_pydantic_schemas PASSED     [ 96%]
backend/tests/test_user_models.py::test_therapist_pydantic_schemas PASSED [100%]

======================= 28 passed, 5 warnings in 1.26s ========================
```

### Regression Verification on Existing Chatbot Code
```bash
pytest chatbot/tests/test_v2_adapter.py chatbot/tests/test_behaviour_adapter.py -v
```
Output:
```text
======================= 18 passed, 5 warnings in 6.53s ========================
```
- Zero files in `chatbot/` or `engine/` were modified.
