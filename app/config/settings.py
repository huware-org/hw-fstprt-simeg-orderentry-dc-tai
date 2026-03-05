"""Environment configuration loader for Cloud Run deployment."""

import logging
import sys
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    GEMINI_API_KEY: str
    PORT: int = 8080
    FRONTEND_URL: str = "*"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instantiate settings to be imported across the app
settings = Settings()


# Configure logging
def setup_logger(name: str = "simeg") -> logging.Logger:
    """
    Setup and configure application logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    if settings.ENVIRONMENT == "development":
        # Detailed format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # JSON-like format for production (Cloud Run)
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","file":"%(filename)s","line":%(lineno)d,"message":"%(message)s"}',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Create default logger instance
logger = setup_logger()
