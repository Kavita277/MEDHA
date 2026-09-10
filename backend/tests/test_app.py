"""
Application Startup & Foundation Tests
======================================

Verifies:
- Application starts up successfully and serves root metadata
- API version routing under /api/v1
- 404 handling follows normalized error schema
- CORS headers in responses
- Configuration loading and settings defaults
"""

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings, get_settings
from backend.main import app, create_application


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_app_startup_and_root(client):
    """Verifies application starts up and root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["api_v1"] == "/api/v1"
    assert data["docs"] == "/docs"


def test_api_version_routing(client):
    """Verifies that endpoints are correctly prefixed under /api/v1."""
    # /api/v1/health should exist
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    # /api/v1/ready should exist
    response = client.get("/api/v1/ready")
    assert response.status_code == 200


def test_not_found_error_handling(client):
    """Verifies normalized 404 error schema on non-existent endpoints."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data


def test_cors_headers_configured(client):
    """Verifies that CORS middleware is active and sets appropriate headers."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_process_time_header(client):
    """Verifies that response timing middleware adds X-Process-Time-Ms header."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-process-time-ms" in response.headers


def test_settings_configuration():
    """Verifies configuration loading and environment properties."""
    settings = get_settings()
    assert isinstance(settings.PROJECT_NAME, str)
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_application_factory():
    """Verifies that create_application creates a clean, working instance."""
    test_app = create_application()
    with TestClient(test_app) as test_client:
        res = test_client.get("/api/v1/health")
        assert res.status_code == 200
