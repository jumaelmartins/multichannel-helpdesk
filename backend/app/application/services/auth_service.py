from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.infra.database.repositories.user_repository import UserRepository


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in user.items() if k != "password_hash"}


class AuthService:
    def __init__(self, db: AsyncDatabase):
        self.users = UserRepository(db)

    async def login(self, email: str, password: str) -> dict[str, Any]:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise UnauthorizedError("Invalid email or password")
        return self._token_response(user)

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        payload = decode_token(refresh_token, expected_type="refresh")
        user = await self.users.get(payload["sub"])
        if not user:
            raise UnauthorizedError("User no longer exists")
        return self._token_response(user)

    async def get_user(self, user_id: str) -> dict[str, Any]:
        user = await self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return _public_user(user)

    def _token_response(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "access_token": create_access_token(
                user["id"], user["role"], user.get("tenant_id")
            ),
            "refresh_token": create_refresh_token(user["id"]),
            "token_type": "bearer",
            "user": _public_user(user),
        }
