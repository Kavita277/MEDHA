"""
MEDHA Backend Configuration
===========================

Centralized, typed configuration management for the MEDHA FastAPI backend.
Loads settings from environment variables and .env file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file from repository root if present
load_dotenv()


class Settings(BaseModel):
    """Application settings and environment configuration."""

    # Project Information
    PROJECT_NAME: str = "MEDHA Backend API"
    PROJECT_DESCRIPTION: str = "Enterprise Trauma-Informed Conversational & Clinical Risk Backend Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment & Debugging
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("MEDHA_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    )
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    )

    # Server Configuration
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # CORS Configuration
    # Defaults allow local Streamlit, Next.js, and standard dev hosts
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost,http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8081,http://127.0.0.1:8081",
            ).split(",")
            if origin.strip()
        ]
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )

    # Database Configuration (PostgreSQL / SQLAlchemy)
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "")
    )
    POSTGRES_SERVER: str = Field(
        default_factory=lambda: os.getenv("POSTGRES_SERVER", "localhost")
    )
    POSTGRES_PORT: int = Field(
        default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432"))
    )
    POSTGRES_USER: str = Field(
        default_factory=lambda: os.getenv("POSTGRES_USER", "postgres")
    )
    POSTGRES_PASSWORD: str = Field(
        default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    POSTGRES_DB: str = Field(
        default_factory=lambda: os.getenv("POSTGRES_DB", "medha_db")
    )
    DB_POOL_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10"))
    )
    DB_MAX_OVERFLOW: int = Field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )
    DB_POOL_TIMEOUT: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30"))
    )
    DB_ECHO: bool = Field(
        default_factory=lambda: os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")
    )

    # Optional Gemini Key for later steps
    GEMINI_API_KEY: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    )

    # --- Authentication & JWT Security ---
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "medha-insecure-dev-jwt-secret-change-in-production-1234567890")
    )
    JWT_ALGORITHM: str = Field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256")
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    )

    # --- Behaviour Configuration ---
    BEHAVIOUR_LATE_NIGHT_START_HOUR: int = Field(
        default_factory=lambda: int(os.getenv("BEHAVIOUR_LATE_NIGHT_START_HOUR", "0"))
    )
    BEHAVIOUR_LATE_NIGHT_END_HOUR: int = Field(
        default_factory=lambda: int(os.getenv("BEHAVIOUR_LATE_NIGHT_END_HOUR", "6"))
    )
    BEHAVIOUR_LATE_NIGHT_TIMEZONE: str = Field(
        default_factory=lambda: os.getenv("BEHAVIOUR_LATE_NIGHT_TIMEZONE", "UTC")
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Constructs the SQLAlchemy database URI.
        Prioritizes DATABASE_URL if set. If not, constructs from individual POSTGRES_* fields.
        Normalizes postgres:// -> postgresql:// for SQLAlchemy 2.0.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url

        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton provider for application settings."""
    return Settings()
