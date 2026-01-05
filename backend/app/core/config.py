"""
Configuration Management

Purpose:
    Loads application global settings from environment variables.
    Centralizes all configuration like Database URL, API Keys, and Project Strings.

Dependencies:
    - uses `pydantic-settings` to robustly parse .env files.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus

class Settings(BaseSettings):
    """
    Global application settings.
    Fields without defaults will raise an error if missing from .env.
    """
    PROJECT_NAME: str = "AI Exam System"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "exam_evaluation_db"
    POSTGRES_PORT: str = "5432"

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Constructs the async PostgreSQL connection string.
        Uses `quote_plus` to safely handle special characters (like @, :) in passwords.
        """
        encoded_user = quote_plus(self.POSTGRES_USER)
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{encoded_user}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        # Optional: extra="ignore" can be added if we want to ignore extra env vars

settings = Settings()
