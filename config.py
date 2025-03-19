"""
Configuration management for the Multi-Model AI API Integration System.
Uses Pydantic settings to load and validate configuration from environment variables.
"""
from functools import lru_cache
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Application settings
    app_name: str = "Multi-Model AI API Integration"
    app_env: Literal["development", "testing", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # Database settings
    database_url: str = "sqlite:///./data/multi_model_ai.db"
    
    # If using PostgreSQL with Docker:
    # postgres_user: str = "postgres"
    # postgres_password: str = "postgres"
    # postgres_db: str = "multi_model_ai"
    # postgres_host: str = "db"  # service name in docker-compose
    # postgres_port: str = "5432"
    
    @property
    def postgres_dsn(self) -> str:
        """Get PostgreSQL connection string (for Docker setup)"""
        if hasattr(self, 'postgres_host'):
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        return ""
    
    # Security settings
    secret_key: str = "replace_with_secure_random_string_in_production"
    token_expire_minutes: int = 60
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # API Keys (optional, can be provided through UI)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    
    # Configure env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Create cached instance of settings.
    Using lru_cache to avoid loading .env file for each request
    """
    return Settings()