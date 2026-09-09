import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MEDHA AI Dynamic Mental Health Monitoring System"
    API_V1_STR: str = "/api"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./medha.db"

    class Config:
        env_file = ".env"

settings = Settings()
