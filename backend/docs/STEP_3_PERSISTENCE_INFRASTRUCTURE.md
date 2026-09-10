# MEDHA Backend — Step 3: Persistence Infrastructure Summary Document

## 1. Executive Summary

In **STEP 3** of the MEDHA backend development plan, the core database persistence infrastructure was established using:
- **PostgreSQL** as the primary enterprise database engine.
- **SQLAlchemy 2.0** (`DeclarativeBase`, typed `Mapped` attributes, scoped sessionmaker, and connection pooling).
- **Alembic** for schema migrations and version-controlled revision histories.

All components were implemented strictly following the principle of minimum necessary infrastructure:
- Core connection, engine factory, session lifecycle, declarative base, and generic repository abstractions were built.
- **Zero business models** (User, Case, Session, Chat, Audit) were created in this step, ensuring clean separation for Step 4.
- **Zero modifications** were made to `chatbot/` or `engine/` codebases.
- 100% test coverage was achieved across configuration, engine creation, connection health checks, session lifecycle, mixins, repository CRUD, and Alembic configuration.

---

## 2. Directory & File Manifest

### New Files Created
| File Path | Purpose |
| :--- | :--- |
| `backend/persistence/__init__.py` | Package root exporting engine, SessionLocal, `get_db`, `Base`, and `BaseRepository`. |
| `backend/persistence/base.py` | SQLAlchemy 2.0 `Base(DeclarativeBase)` and reusable UTC `TimestampMixin`. |
| `backend/persistence/database.py` | Engine builder, connection pooling, SessionLocal factory, FastAPI `get_db` dependency, health check. |
| `backend/persistence/models/__init__.py` | Package initialized for future ORM models; currently re-exports `Base` and `TimestampMixin`. |
| `backend/persistence/repositories/__init__.py` | Generic `BaseRepository[ModelType]` providing standard typed CRUD abstraction. |
| `alembic.ini` | Root Alembic configuration specifying migration script locations and logging. |
| `backend/persistence/migrations/env.py` | Alembic runtime environment script bound to `backend.config.Settings` and `Base.metadata`. |
| `backend/persistence/migrations/script.py.mako` | Template for generating versioned migration files. |
| `backend/persistence/migrations/README` | Documentation for migration directory usage. |
| `backend/persistence/migrations/versions/.gitkeep` | Placeholder ensuring revision directory is tracked in Git. |
| `backend/tests/test_database.py` | 10 unit tests covering configuration, pooling, sessions, Base, repository, and Alembic. |
| `backend/docs/STEP_3_PERSISTENCE_INFRASTRUCTURE.md` | This summary document. |

### Existing Files Updated
| File Path | Changes Made |
| :--- | :--- |
| `backend/config.py` | Added PostgreSQL and SQLAlchemy configuration fields (`DATABASE_URL`, `POSTGRES_*`, `DB_POOL_*`, `DB_ECHO`) and `SQLALCHEMY_DATABASE_URI` property. |
| `backend/dependencies.py` | Re-exported `get_db` database session dependency alongside `get_app_settings`. |
| `.env.example` | Documented all database connection and pooling environment variables, host/port, and CORS settings. |

---

## 3. Architecture & Key Design Decisions

### 3.1 Dual-Mode Engine Configuration (`backend/persistence/database.py`)
The engine builder dynamically configures the database connection based on the dialect:
- **PostgreSQL (Production/Staging)**:
  - Connection pooling with `pool_size` (default: 10) and `max_overflow` (default: 20).
  - Liveness verification via `pool_pre_ping=True` to eliminate stale connections.
  - Connection timeout configured via `pool_timeout` (default: 30s).
- **SQLite (Unit Tests & In-Memory Verification)**:
  - Automatically applies `connect_args={"check_same_thread": False}` without pooling parameters that SQLite does not support.

### 3.2 Dynamic Settings & URI Resolution (`backend/config.py`)
- `Settings.SQLALCHEMY_DATABASE_URI`:
  - If `DATABASE_URL` is explicitly provided, it is used directly (with automatic normalization of `postgres://` to `postgresql://` required by SQLAlchemy 2.0).
  - If `DATABASE_URL` is omitted, the URI is synthesized from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, and `POSTGRES_DB` using the standard `postgresql+psycopg2` driver.

### 3.3 FastAPI Dependency Injection (`get_db`)
The `get_db()` generator provides a scoped database session per HTTP request:
```python
def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
This guarantees that sessions are deterministically closed even if an exception occurs during request execution.

### 3.4 Declarative Base & TimestampMixin (`backend/persistence/base.py`)
- `Base`: Single declarative base subclassing `DeclarativeBase`, unifying model metadata for Alembic discovery.
- `TimestampMixin`: Reusable class providing `created_at` and `updated_at` columns initialized with timezone-aware UTC timestamps (`_current_utc_timestamp`).

### 3.5 Generic Repository Pattern (`backend/persistence/repositories/__init__.py`)
A type-safe `BaseRepository[ModelType]` provides standard data access methods:
- `get(id)`
- `list(skip, limit)`
- `add(obj)`
- `delete(obj)`
Future domain-specific repositories (e.g. `UserRepository`, `CaseRepository`, `ChatSessionRepository`) will inherit from this base class.

### 3.6 Alembic Migration Setup (`alembic.ini`, `backend/persistence/migrations/`)
- `script_location = backend/persistence/migrations`
- `env.py` dynamically imports `get_settings()` from `backend.config` and extracts `Settings().SQLALCHEMY_DATABASE_URI`.
- `target_metadata = Base.metadata` binds Alembic autogeneration directly to all registered SQLAlchemy models.

---

## 4. Environment Variables Documented (`.env.example`)

The following variables have been added and documented in `.env.example`:

```bash
# --- Database & Persistence Configuration (PostgreSQL / SQLAlchemy) ---
# Primary PostgreSQL connection settings
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=medha_db

# Optional direct connection URL (overrides individual POSTGRES_* settings if set)
# Examples:
#   PostgreSQL: postgresql+psycopg2://postgres:postgres@localhost:5432/medha_db
#   SQLite (for testing/local development): sqlite:///./medha_dev.db
DATABASE_URL=

# SQLAlchemy Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false
```

---

## 5. Verification & Test Results

### 5.1 Backend Test Suite Execution
Command:
```bash
pytest backend/tests -v
```
Output:
```text
backend/tests/test_app.py::test_app_startup_and_root PASSED              [  5%]
backend/tests/test_app.py::test_api_version_routing PASSED               [ 11%]
backend/tests/test_app.py::test_not_found_error_handling PASSED          [ 17%]
backend/tests/test_app.py::test_cors_headers_configured PASSED           [ 23%]
backend/tests/test_app.py::test_process_time_header PASSED               [ 29%]
backend/tests/test_app.py::test_settings_configuration PASSED            [ 35%]
backend/tests/test_app.py::test_application_factory PASSED               [ 41%]
backend/tests/test_database.py::test_default_database_uri_generation PASSED [ 47%]
backend/tests/test_database.py::test_database_url_override_and_normalization PASSED [ 52%]
backend/tests/test_database.py::test_build_engine_sqlite PASSED          [ 58%]
backend/tests/test_database.py::test_check_db_connection PASSED          [ 64%]
backend/tests/test_database.py::test_get_db_yield_and_close PASSED       [ 70%]
backend/tests/test_database.py::test_model_timestamps PASSED             [ 76%]
backend/tests/test_database.py::test_base_repository_crud PASSED         [ 82%]
backend/tests/test_database.py::test_alembic_configuration_validity PASSED [ 88%]
backend/tests/test_health.py::test_health_endpoint PASSED                [ 94%]
backend/tests/test_health.py::test_readiness_endpoint PASSED             [100%]

======================== 17 passed, 1 warning in 1.11s ========================
```

### 5.2 Alembic CLI Verification
- `python -m alembic branches` exited with code `0`.
- `python -m alembic heads` exited with code `0`.

### 5.3 System Isolation & Regression Check
- `chatbot/tests/test_medha_state.py` executed and passed 13/13 tests without issues.
- `git status` confirms zero modifications to `chatbot/` or `engine/`.

---

## 6. Current Status & Next Steps

**STEP 3 is 100% COMPLETE.** Execution is halted as requested.

**Next Step (STEP 4)**:
- Define domain models in `backend/persistence/models/`:
  - User model & role enumeration
  - Patient / Case model
  - Chat Session & Message models
  - Risk Assessment / Audit Log models
- Generate initial Alembic revision (`alembic revision --autogenerate -m "create_initial_schema"`).
