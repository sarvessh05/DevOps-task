import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AeroFlow"
    API_V1_STR: str = "/api/v1"
    
    # DB & Redis connection strings
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/aeroflow"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # AI Config
    GEMINI_API_KEY: str = ""
    
    # Paths
    UPLOAD_DIR: str = "uploads"
    
    # Celery configuration
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Pydantic Settings settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
