"""
Health & Readiness Endpoint Tests
=================================

Verifies:
- GET /api/v1/health returns 200 OK with valid schema
- GET /api/v1/ready returns 200 OK with valid checks
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Verifies that GET /api/v1/health returns status 'ok' and valid metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "service" in data
    
    settings = get_settings()
    assert data["version"] == settings.VERSION
    assert data["environment"] == settings.ENVIRONMENT


def test_readiness_endpoint(client):
    """Verifies that GET /api/v1/ready returns status 'ready' and check results."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert isinstance(data["checks"], dict)
    assert data["checks"].get("api_router") == "ok"
    assert data["checks"].get("configuration") == "loaded"
