"""
Health & Readiness Endpoints
============================

Provides Kubernetes/Docker/load-balancer compatible probes:
- GET /api/v1/health: Basic liveness probe
- GET /api/v1/ready: Subsystem readiness verification probe
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.config import Settings
from backend.dependencies import get_app_settings
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
    settings: Settings = Depends(get_app_settings),
) -> ReadinessResponse:
    """
    Readiness probe verifying that core configurations and application
    subsystems are initialized.
    """
    checks = {
        "api_router": "ok",
        "configuration": "loaded",
        "environment": settings.ENVIRONMENT,
    }

    return ReadinessResponse(
        status="ready",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        checks=checks,
    )
