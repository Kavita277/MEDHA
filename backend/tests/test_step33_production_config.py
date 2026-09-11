"""
MEDHA Backend Step 33 — Production Configuration Tests
=====================================================

Authoritative specification: backend/docs/backend_plan.md §33

Tests production configuration, environment loading, deployment hardening,
storage settings, readiness probes, and fail-fast startup validation.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.config import ConfigurationError, Settings, get_settings
from backend.main import create_application, lifespan
from backend.security.tokens import create_access_token, decode_access_token


# ============================================================================
# 1. Development & Default Configuration
# ============================================================================

def test_development_default_configuration():
    """
    Verifies that in default development mode, settings load safe defaults
    and do not raise validation errors.
    """
    settings = Settings(ENVIRONMENT="development")
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.is_staging is False

    # Development validation does not fail with default dev keys
    errors = settings.validate_production_settings(raise_on_error=False)
    # Should not raise in development even if keys are dev-defaults
    assert isinstance(errors, list)


# ============================================================================
# 2. Production JWT Validation
# ============================================================================

def test_production_jwt_validation_rejects_insecure_defaults():
    """
    In production mode, the default insecure development JWT secret
    must be strictly rejected.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://app_user:strong_pwd@db.internal:5432/medha_prod",
        GEMINI_API_KEY="prod-dummy-gemini-key-for-presence-test",
        CORS_ORIGINS=["https://app.medha.health"],
        # Default dev JWT secret
        JWT_SECRET_KEY="medha-insecure-dev-jwt-secret-change-in-production-1234567890",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_production_settings(raise_on_error=True)

    err_msg = str(exc_info.value)
    assert "JWT" in err_msg
    assert "Insecure development JWT_SECRET_KEY cannot be used in production" in err_msg
    # Sensitive secret value must never appear in error message
    assert "medha-insecure-dev-jwt-secret" not in err_msg


def test_production_jwt_validation_rejects_empty_secret():
    """
    In production mode, an empty or whitespace JWT secret must be rejected.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://app_user:strong_pwd@db.internal:5432/medha_prod",
        GEMINI_API_KEY="prod-dummy-gemini-key-for-presence-test",
        CORS_ORIGINS=["https://app.medha.health"],
        JWT_SECRET_KEY="   ",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_production_settings(raise_on_error=True)

    err_msg = str(exc_info.value)
    assert "JWT: JWT_SECRET_KEY must not be empty in production" in err_msg


# ============================================================================
# 3. Production Database Validation
# ============================================================================

def test_production_database_validation_rejects_sqlite():
    """
    In production mode, SQLite database URLs (file or in-memory)
    must be strictly prohibited.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="sqlite:///./prod_mistake.db",
        JWT_SECRET_KEY="production-secure-random-secret-key-32chars",
        GEMINI_API_KEY="prod-dummy-gemini-key-for-presence-test",
        CORS_ORIGINS=["https://app.medha.health"],
    )

    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_production_settings(raise_on_error=True)

    err_msg = str(exc_info.value)
    assert "DATABASE: SQLite database URL is prohibited in production" in err_msg
    # Connection string details must not be leaked
    assert "prod_mistake.db" not in err_msg


def test_production_database_validation_rejects_empty_url():
    """
    In production mode, missing or empty database configuration must be rejected.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="",
        POSTGRES_SERVER="",
        POSTGRES_DB="",
        JWT_SECRET_KEY="production-secure-random-secret-key-32chars",
        GEMINI_API_KEY="prod-dummy-gemini-key-for-presence-test",
        CORS_ORIGINS=["https://app.medha.health"],
    )
    # Force empty URI
    with patch.object(Settings, "SQLALCHEMY_DATABASE_URI", ""):
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_production_settings(raise_on_error=True)
        assert "DATABASE: Production requires a configured database URL" in str(exc_info.value)


def test_production_database_validation_accepts_valid_postgresql():
    """
    Valid PostgreSQL configuration with all production settings succeeds.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://valid_user:valid_pwd@db.host.internal:5432/medha_production",
        JWT_SECRET_KEY="production-secure-random-secret-key-32chars",
        GEMINI_API_KEY="prod-dummy-gemini-key-for-presence-test",
        CORS_ORIGINS=["https://app.medha.health"],
    )

    errors = settings.validate_production_settings(raise_on_error=True)
    assert errors == []


# ============================================================================
# 4. Token Expiration Configuration
# ============================================================================

def test_token_expiration_configuration():
    """
    Verifies that custom ACCESS_TOKEN_EXPIRE_MINUTES is loaded and respected
    when creating access tokens.
    """
    custom_minutes = 45
    settings = Settings(
        ACCESS_TOKEN_EXPIRE_MINUTES=custom_minutes,
        JWT_SECRET_KEY="custom-test-secret-for-token-exp-testing",
    )

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    with patch("backend.security.tokens.get_settings", return_value=settings):
        token = create_access_token(
            subject=str(uuid.uuid4()),
            role="USER",
        )

        payload = decode_access_token(token)
        assert payload is not None
        exp_epoch = payload.get("exp")
        assert exp_epoch is not None

        # Expiration should be roughly now + 45 minutes (allow +/- 30s clock skew)
        expected_exp = now_epoch + (custom_minutes * 60)
        assert abs(exp_epoch - expected_exp) < 30


# ============================================================================
# 5. Storage Configuration
# ============================================================================

def test_storage_configuration_defaults_and_readiness(tmp_path: Path):
    """
    Verifies storage configuration loading, upload directory creation,
    and safe temporary probe execution.
    """
    test_upload_dir = str(tmp_path / "medha_test_uploads")
    custom_size = 20 * 1024 * 1024  # 20 MB

    settings = Settings(
        STORAGE_BACKEND="local",
        UPLOAD_DIR=test_upload_dir,
        MAX_AUDIO_SIZE_BYTES=custom_size,
    )

    assert settings.STORAGE_BACKEND == "local"
    assert settings.UPLOAD_DIR == test_upload_dir
    assert settings.MAX_AUDIO_SIZE_BYTES == custom_size

    # Directory does not exist yet
    assert not Path(test_upload_dir).exists()

    # check_storage_readiness creates directory and cleans up probe
    ready = settings.check_storage_readiness()
    assert ready is True
    assert Path(test_upload_dir).is_dir()

    # Ensure no leftover probe files remain
    probe_files = list(Path(test_upload_dir).glob(".probe_*"))
    assert len(probe_files) == 0


def test_storage_configuration_unusable_path():
    """
    Verifies check_storage_readiness returns False gracefully if upload dir is unusable.
    """
    # Use an impossible path or mock failure
    settings = Settings(UPLOAD_DIR="/path/that/cannot/exist/on/any/machine/nil\x00/bad")
    ready = settings.check_storage_readiness()
    assert ready is False


# ============================================================================
# 6. CORS Configuration & Parsing
# ============================================================================

def test_cors_origins_parsing(monkeypatch):
    """
    Verifies that CORS_ORIGINS is parsed cleanly from comma-separated values,
    handles single origins, multiple origins, and strips whitespace.
    """
    raw_env = "  https://medha.health ,  https://app.medha.health,http://localhost:3000   "
    monkeypatch.setenv("CORS_ORIGINS", raw_env)

    settings = Settings()
    expected = [
        "https://medha.health",
        "https://app.medha.health",
        "http://localhost:3000",
    ]
    assert settings.CORS_ORIGINS == expected


def test_cors_wildcard_rejected_in_production():
    """
    In production mode, wildcard '*' origins must be rejected to prevent
    unauthorized cross-origin access.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://app_user:pwd@db:5432/prod",
        JWT_SECRET_KEY="production-secure-random-secret-key-32chars",
        GEMINI_API_KEY="prod-dummy-gemini-key",
        CORS_ORIGINS=["*"],
    )

    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_production_settings(raise_on_error=True)

    assert "CORS: Wildcard '*' origin is prohibited in production" in str(exc_info.value)


# ============================================================================
# 7. Production Gemini Validation
# ============================================================================

def test_production_gemini_validation_rejects_missing_key():
    """
    In production mode, missing or empty GEMINI_API_KEY must be rejected.
    """
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://app_user:pwd@db:5432/prod",
        JWT_SECRET_KEY="production-secure-random-secret-key-32chars",
        CORS_ORIGINS=["https://app.medha.health"],
        GEMINI_API_KEY="",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_production_settings(raise_on_error=True)

    assert "GEMINI: GEMINI_API_KEY must be configured in production" in str(exc_info.value)


def test_gemini_settings_unified():
    """
    Verifies that GEMINI_MODEL and GEMINI_TIMEOUT_SECONDS load correctly.
    """
    settings = Settings(
        GEMINI_MODEL="gemini-2.5-pro",
        GEMINI_TIMEOUT_SECONDS=60,
    )
    assert settings.GEMINI_MODEL == "gemini-2.5-pro"
    assert settings.GEMINI_TIMEOUT_SECONDS == 60


# ============================================================================
# 8. Readiness Probe — Healthy State
# ============================================================================

def test_readiness_probe_healthy(client: TestClient):
    """
    Verifies that GET /api/v1/ready returns HTTP 200 and status 'ready'
    when the database and configuration are healthy.
    Ensures no secrets or credentials are exposed in response.
    """
    response = client.get("/api/v1/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    checks = data["checks"]
    assert checks.get("api_router") == "ok"
    assert checks.get("configuration") == "loaded"
    assert checks.get("database") == "connected"
    assert checks.get("storage") == "ready"

    # Verify no secret/credential leaks in raw response text
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "secret" not in raw_text
    assert "psycopg2" not in raw_text


# ============================================================================
# 9. Readiness Probe — Unhealthy State (DB Failure Seam)
# ============================================================================

def test_readiness_probe_unhealthy_when_db_down(client: TestClient, monkeypatch):
    """
    Simulates database connectivity failure using the existing check_db_connection seam.
    Verifies:
    - returns HTTP 503 SERVICE_UNAVAILABLE
    - status is 'unhealthy'
    - diagnostic check indicates 'unreachable'
    - response text contains no credentials, connection strings, or stack traces
    """
    # Monkeypatch the database connectivity check in the endpoint module
    monkeypatch.setattr(
        "backend.api.v1.endpoints.health.check_db_connection",
        lambda *args, **kwargs: False,
    )

    response = client.get("/api/v1/ready")
    assert response.status_code == 503

    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "unreachable"

    # Verify safe output
    raw_text = response.text.lower()
    assert "traceback" not in raw_text
    assert "password" not in raw_text
    assert "postgres" not in raw_text


# ============================================================================
# 10. Startup Validation in Lifespan
# ============================================================================

@pytest.mark.asyncio
async def test_startup_validation_fails_fast_in_production(monkeypatch):
    """
    Verifies that application startup fails fast during FastAPI lifespan
    when ENVIRONMENT=production and critical settings are invalid.
    """
    # Configure production environment with insecure dev secret
    bad_prod_settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="sqlite:///./bad.db",
        JWT_SECRET_KEY="medha-insecure-dev-jwt-secret-change-in-production-1234567890",
        GEMINI_API_KEY="",
    )

    monkeypatch.setattr("backend.main.get_settings", lambda: bad_prod_settings)

    test_app = create_application()
    with pytest.raises(ConfigurationError) as exc_info:
        async with lifespan(test_app):
            pass

    assert "Production configuration validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_startup_validation_succeeds_in_development():
    """
    Verifies that in development mode, application startup succeeds
    without failing due to missing production secrets.
    """
    dev_settings = Settings(ENVIRONMENT="development")
    with patch("backend.main.get_settings", return_value=dev_settings):
        test_app = create_application()
        async with lifespan(test_app):
            # Startup was successful
            pass


# ============================================================================
# 11. Environment Selection
# ============================================================================

def test_environment_selection_properties():
    """
    Verifies is_development, is_staging, and is_production properties.
    """
    dev = Settings(ENVIRONMENT="development")
    assert dev.is_development is True
    assert dev.is_production is False
    assert dev.is_staging is False

    staging = Settings(ENVIRONMENT="staging")
    assert staging.is_development is False
    assert staging.is_production is False
    assert staging.is_staging is True

    prod = Settings(ENVIRONMENT="production")
    assert prod.is_development is False
    assert prod.is_production is True
    assert prod.is_staging is False


# ============================================================================
# 12. Logging Configuration & Secret Protection
# ============================================================================

def test_logging_configuration_loading():
    """
    Verifies that LOG_LEVEL is normalized and loaded from settings.
    """
    settings = Settings(LOG_LEVEL="debug")
    assert settings.LOG_LEVEL == "DEBUG"

    settings_warn = Settings(LOG_LEVEL="warning")
    assert settings_warn.LOG_LEVEL == "WARNING"
