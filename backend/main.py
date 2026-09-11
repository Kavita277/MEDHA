"""
MEDHA Backend API Service
=========================

Main application entry point for the enterprise FastAPI backend.
Configures:
- Application lifecycle and metadata
- /api/v1 routing hierarchy
- CORS middleware for development and production
- Structured logging and request tracing
- Global exception handling and normalized error responses
- Health and readiness probes
"""

from __future__ import annotations

import logging
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.v1.router import api_v1_router
from backend.config import Settings, get_settings
from backend.jobs.prediction_queue import process_queue, reset_queue
from backend.security.redaction import (
    sanitize_url,
    sanitize_validation_errors,
    mask_internal_error,
)



# ===========================================================================
# 1. STRUCTURED LOGGING CONFIGURATION
# ===========================================================================

def setup_logging(settings: Settings) -> None:
    """Configures structured console logging across the application."""
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logging_format = (
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=logging_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


logger = logging.getLogger("backend.main")


# ===========================================================================
# 2. LIFESPAN CONTEXT MANAGER
# ===========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and graceful shutdown hooks."""
    settings = get_settings()
    setup_logging(settings)

    # Fail fast on startup in production if critical configuration is invalid
    if settings.is_production:
        settings.validate_production_settings()

    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} "
        f"[env={settings.ENVIRONMENT}, debug={settings.DEBUG}]"
    )
    
    reset_queue()
    worker_task = asyncio.create_task(process_queue())
    
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


# ===========================================================================
# 3. APPLICATION FACTORY
# ===========================================================================

def create_application() -> FastAPI:
    """Factory creating and configuring the primary FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # Development CORS Middleware
    # -----------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Request Timing / Tracing Middleware
    # -----------------------------------------------------------------------
    @app.middleware("http")
    async def log_request_timing(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        
        # Log HTTP access with sanitized query string
        client_ip = request.client.host if request.client else "unknown"
        sanitized_uri = sanitize_url(str(request.url.path) + (f"?{request.url.query}" if request.url.query else ""))
        logger.info(
            f"{client_ip} - \"{request.method} {sanitized_uri}\" "
            f"{response.status_code} ({process_time_ms:.2f}ms)"
        )
        return response

    # -----------------------------------------------------------------------
    # Global Exception Handlers
    # -----------------------------------------------------------------------
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        masked_detail = mask_internal_error(str(exc.detail))
        sanitized_path = sanitize_url(str(request.url.path))
        logger.warning(f"HTTP {exc.status_code} on {sanitized_path}: {masked_detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": masked_detail,
                "path": sanitized_path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        sanitized_errors = sanitize_validation_errors(exc.errors())
        sanitized_path = sanitize_url(str(request.url.path))
        logger.warning(f"Validation error on {sanitized_path}: {sanitized_errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": "Request validation failed",
                "errors": sanitized_errors,
                "path": sanitized_path,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        sanitized_path = sanitize_url(str(request.url.path))
        logger.error(f"Unhandled exception on {sanitized_path}: {mask_internal_error(str(exc))}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error occurred.",
                "path": sanitized_path,
            },
        )


    # -----------------------------------------------------------------------
    # Router Mounts
    # -----------------------------------------------------------------------
    # Mount /api/v1
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Root informational endpoint
    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "api_v1": settings.API_V1_STR,
            "docs": "/docs",
        }

    return app


# Application Instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    app_settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=app_settings.is_development,
    )
