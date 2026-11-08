"""Pytest global configuration and environment setup."""

import os
from pathlib import Path

# Load .env if present
env_paths = [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        break

# Default fallbacks for CI / testing if not set
test_defaults = {
    "APP_ENV": "test",
    "DEBUG": "true",
    "DATABASE_URL": "postgresql://quiz_user:test_password_local_123@127.0.0.1:5432/quiz_dev",
    "DATABASE_URL_DIRECT": "postgresql://quiz_user:test_password_local_123@127.0.0.1:5432/quiz_dev",
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
