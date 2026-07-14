from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _create_token(claims: dict[str, Any], expires_in: int, token_type: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        **claims,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str, tenant_id: str | None = None) -> str:
    settings = get_settings()
    claims: dict[str, Any] = {"sub": user_id, "role": role}
    if tenant_id:
        claims["tenant_id"] = tenant_id
    return _create_token(claims, settings.jwt_expires_in, "access")


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token({"sub": user_id}, settings.jwt_refresh_expires_in, "refresh")


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Invalid token type")
    return payload
