"""Application configuration module using pydantic-settings.

Provides startup validation for database, JWT security parameters, and CORS settings.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings container for Enterprise AI Research Engine backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = Field(default="development", description="Application environment")
    API_HOST: str = Field(default="0.0.0.0", description="Host address for server")
    API_PORT: int = Field(default=8000, description="Server listening port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    DEBUG: bool = Field(default=True, description="Debug mode toggle")

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed origins for CORS",
    )

    # Database Settings
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="ai_research_db", description="PostgreSQL database name")
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./test_ai_research.db",
        description="SQLAlchemy Database URL (Async driver)",
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./test_ai_research.db",
        description="SQLAlchemy Sync Database URL for migrations",
    )

    # Security & JWT Configuration
    SECRET_KEY: str = Field(
        default="e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9",
        description="Secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT hashing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")

    # Cookie Security Settings
    COOKIE_SECURE: bool = Field(default=False, description="Set Secure flag on HttpOnly cookies")
    COOKIE_SAMESITE: str = Field(default="lax", description="SameSite policy for HttpOnly cookies")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated string or JSON list for CORS origins."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    def validate_startup_security(self) -> None:
        """Validate required environment variables on startup.

        Raises:
            ValueError: If a critical environment variable is missing or insecure.
        """
        insecure_keys = ["secret", "change_me", "12345", "admin", "password"]
        if not self.SECRET_KEY or any(self.SECRET_KEY.lower() == k for k in insecure_keys):
            raise ValueError("SECRET_KEY must be configured with a secure random key.")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")


settings = Settings()
