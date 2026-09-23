"""
Health & Readiness Endpoints
============================

Provides Kubernetes/Docker/load-balancer compatible probes:
- GET /api/v1/health: Basic liveness probe
- GET /api/v1/ready: Subsystem readiness verification probe
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from backend.config import Settings
from backend.dependencies import get_app_settings
from backend.persistence.database import check_db_connection
from backend.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Returns 200 OK if the application server is up and accepting HTTP traffic.",
)
async def get_health(
    settings: Settings = Depends(get_app_settings),
) -> HealthResponse:
    """Liveness probe verifying that the FastAPI server is responsive."""
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Returns 200 OK when the application and all required initial configurations are ready to serve requests.",
)
async def get_readiness(
    response: Response,
    settings: Settings = Depends(get_app_settings),
) -> ReadinessResponse:
    """
    Readiness probe verifying that core configurations, database connectivity,
    and storage subsystems are initialized and accepting traffic.
    Returns HTTP 200 when ready, HTTP 503 when critical dependencies fail.
    Never exposes internal secrets or connection credentials.
    """
    checks = {
        "api_router": "ok",
        "configuration": "loaded",
        "environment": settings.ENVIRONMENT,
    }

    # 1. Database connectivity check using existing check_db_connection seam
    db_ok = check_db_connection()
    checks["database"] = "connected" if db_ok else "unreachable"

    # 2. Storage subsystem check
    storage_ok = settings.check_storage_readiness()
    checks["storage"] = "ready" if storage_ok else "unusable"

    # 3. Production configuration validation check (if in production)
    config_ok = True
    if settings.is_production:
        errors = settings.validate_production_settings(raise_on_error=False)
        if errors:
            config_ok = False
            checks["configuration"] = "invalid"

    is_ready = db_ok and storage_ok and config_ok

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "unhealthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        checks=checks,
    )
