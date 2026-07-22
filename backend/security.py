"""
backend/security.py
---------------------
비밀번호 해시(표준 라이브러리 hashlib.pbkdf2_hmac, 외부 의존성 없음), 로그인 세션용 JWT,
그리고 에이전트 기기 토큰 해시(고엔트로피 랜덤 토큰이므로 sha256으로 충분) 유틸.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, Optional

import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_SECONDS = 60 * 60 * 24 * 30  # 30일

_PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest_hex = password_hash.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return hmac.compare_digest(expected.hex(), digest_hex)


def create_session_token(user_id: int) -> str:
    payload: Dict[str, Any] = {"sub": str(user_id), "exp": int(time.time()) + JWT_EXPIRES_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def generate_device_code() -> str:
    """사람이 옮겨 적어도 되는 짧은 페어링 코드 (예: 4823-9107)."""
    return f"{secrets.randbelow(10_000):04d}-{secrets.randbelow(10_000):04d}"


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


def hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
