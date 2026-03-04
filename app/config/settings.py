"""Environment configuration loader for Cloud Run deployment."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    GEMINI_API_KEY: str
    PORT: int = 8080
    FRONTEND_URL: str = "*"
    ENVIRONMENT: str = "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instantiate settings to be imported across the app
settings = Settings()
