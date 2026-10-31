import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.
    Validates all mandatory settings on startup.
    """

    # Application Environment
    APP_ENV: str = "development"
    DEBUG: bool = True
    APP_PORT: int = 8000
    DOCS_ENABLED: bool = True

    # Security & Auth
    # SECRET_KEY is mandatory: missing or blank value raises a validation error immediately.
    SECRET_KEY: str = Field(
        default="",
        validate_default=True,
        description="Mandatory cryptographic secret key for tokens and security",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    SESSION_TTL_HOURS: int = 24

    # Quiz Engine Execution Policies (QUIZ.md §9)
    ATTEMPT_GRACE_SECONDS: int = 15  # Grace period for submission network latency
    DATA_RETENTION_DAYS: int = 90  # Logs & transient attempts retention
    MAX_UPLOAD_MB: int = 10  # Max essay file upload limit

    # Database
    DATABASE_URL: str = "postgresql://quiz_user:dhohan_138@localhost:5432/quiz_db"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # S3 / Cloudflare R2 Storage (Optional in local dev)
    S3_ENDPOINT_URL: str | None = None
    S3_BUCKET_NAME: str = "quiz-attachments"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str = "auto"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SECRET_KEY must not be empty or blank")
        return v.strip()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor for application settings singleton."""
    return Settings()


# Export default instance for quick access
settings = get_settings()
