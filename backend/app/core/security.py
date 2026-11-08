"""Security, Password Hashing, Session Token Management, and Rate Limiting.

Implements:
    - Argon2id password hashing with threading.BoundedSemaphore(3) to bound peak RAM.
    - Timing attack mitigation via constant-time dummy password hashing.
    - Cryptographically secure 32-byte session token generation & SHA-256 storage.
    - In-memory failed attempt rate limiter (max 10 failed attempts / min per IP+username).
"""

import hashlib
import secrets
import threading
import time
from collections import defaultdict

import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.errors import AppError

# Argon2id hasher with recommended conservative parameters (~19 MiB RAM per hash)
_ph = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # 19 MiB
    parallelism=1,
    hash_len=32,
    type=argon2.Type.ID,
)

# Semaphore bounding concurrent hash/verify operations to prevent out-of-memory spikes
_hash_semaphore = threading.BoundedSemaphore(3)

# Pre-computed dummy hash generated once at module import for constant-time dummy verify
DUMMY_PASSWORD_HASH: str = _ph.hash("quiz_constant_dummy_password_timing_protection_12345")

# Failed login attempts tracker: (client_ip, username) -> list of timestamp floats
_failed_attempts: dict[tuple[str, str], list[float]] = defaultdict(list)
_failed_lock = threading.Lock()


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id bounded by concurrency semaphore."""
    with _hash_semaphore:
        return _ph.hash(password)


def verify_password(hashed_password: str, plaintext_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash bounded by semaphore."""
    with _hash_semaphore:
        try:
            return _ph.verify(hashed_password, plaintext_password)
        except (VerifyMismatchError, Exception):
            return False


def verify_dummy_password(plaintext_password: str) -> None:
    """Consumes identical CPU & RAM as real verify to prevent timing attacks."""
    with _hash_semaphore:
        try:
            _ph.verify(DUMMY_PASSWORD_HASH, plaintext_password)
        except Exception:
            pass


def generate_session_token() -> str:
    """Generates a cryptographically strong 32-byte URL-safe session token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hexadecimal digest of raw session token for database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def check_failed_login_rate_limit(client_ip: str, username: str) -> None:
    """Enforces rate limit: max 10 failed login attempts per minute per (IP + username).

    Raises AppError(429, 'rate_limited') if threshold is exceeded.
    Other users on the same IP NAT are unaffected.
    """
    key = (client_ip, username.lower())
    now = time.time()
    with _failed_lock:
        timestamps = _failed_attempts[key]
        # Keep only timestamps within the last 60 seconds
        valid_timestamps = [t for t in timestamps if now - t < 60.0]
        _failed_attempts[key] = valid_timestamps

        if len(valid_timestamps) >= 10:
            raise AppError(
                code="rate_limited",
                message="Thử đăng nhập sai quá 10 lần/phút. Vui lòng thử lại sau.",
                status_code=429,
                details={"retry_after_seconds": 60},
            )


def record_failed_login(client_ip: str, username: str) -> None:
    """Records a failed login attempt timestamp for the (IP, username) pair."""
    key = (client_ip, username.lower())
    now = time.time()
    with _failed_lock:
        _failed_attempts[key].append(now)


def clear_failed_logins(client_ip: str, username: str) -> None:
    """Clears failed login records upon successful authentication."""
    key = (client_ip, username.lower())
    with _failed_lock:
        _failed_attempts.pop(key, None)


SAFE_PASSWORD_CHARS = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_random_password(length: int = 8) -> str:
    """Generates an unambiguous, human-friendly random password containing letters and digits.

    Excludes visually ambiguous characters (0, O, I, l, 1).
    """
    while True:
        pwd = "".join(secrets.choice(SAFE_PASSWORD_CHARS) for _ in range(length))
        if any(c.isdigit() for c in pwd) and any(c.isalpha() for c in pwd):
            return pwd
