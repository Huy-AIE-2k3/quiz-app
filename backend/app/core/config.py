"""Application Configuration & Settings Management."""

import sys

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with fail-fast validation for required environment variables."""

    # Environment & Debug
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str

    # Security
    SECRET_KEY: str
    SESSION_TTL_HOURS: int = 12

    # Storage (S3 / R2)
    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str = "auto"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # File Upload Limits
    MAX_UPLOAD_MB: int = 10

    # Data Retention
    DATA_RETENTION_DAYS: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("SECRET_KEY phải dài ít nhất 16 ký tự để đảm bảo an toàn.")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


def load_settings_or_exit() -> Settings:
    """Loads application settings or aborts process with clear error message (no secrets leaked)."""
    try:
        return Settings()  # pyright: ignore
    except ValidationError as exc:
        missing_fields = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "")
            missing_fields.append(f" - {loc}: {msg}")

        formatted_errors = "\n".join(missing_fields)
        sys.stderr.write(
            f"\n[LỖI KHỞI ĐỘNG] Thiếu hoặc sai biến môi trường bắt buộc:\n{formatted_errors}\n"
            f"Vui lòng kiểm tra lại tệp .env hoặc biến môi trường hệ thống.\n\n"
        )
        sys.exit(1)


# Singleton instance
settings: Settings = None  # type: ignore


def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = load_settings_or_exit()
    return settings
