"""Pytest global configuration and environment setup."""

import os

# Set standard testing environment variables before any application module import
test_defaults = {
    "APP_ENV": "test",
    "DEBUG": "true",
    "DATABASE_URL": "postgresql://test:test@127.0.0.1:5432/test_db",
    "DATABASE_URL_DIRECT": "postgresql://test:test@127.0.0.1:5432/test_db",
    "SECRET_KEY": "test_secret_key_minimum_16_characters_long",
    "S3_ENDPOINT": "http://127.0.0.1:9000",
    "S3_BUCKET": "test-bucket",
    "S3_ACCESS_KEY": "test_access",
    "S3_SECRET_KEY": "test_secret",
    "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",
    "MAX_UPLOAD_MB": "10",
}

for key, value in test_defaults.items():
    os.environ.setdefault(key, value)

