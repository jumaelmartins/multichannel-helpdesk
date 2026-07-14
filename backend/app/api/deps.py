from typing import Annotated, Any

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.domain.enums import UserRole
from app.infra.database import mongodb
from app.infra.database.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> AsyncDatabase:
    return mongodb.get_db()


DbDep = Annotated[AsyncDatabase, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> dict[str, Any]:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    payload = decode_token(credentials.credentials)
    user = await UserRepository(db).get(payload["sub"])
    if not user:
        raise UnauthorizedError("User no longer exists")
    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def dependency(user: CurrentUser) -> dict[str, Any]:
        if user["role"] not in roles:
            raise ForbiddenError(f"Requires one of roles: {', '.join(roles)}")
        return user

    return dependency


def scoped_tenant_id(user: dict[str, Any], requested: str | None = None) -> str | None:
    """Force tenant scoping for tenant users; pass through for internal roles."""
    if user["role"] == UserRole.TENANT_USER:
        return user.get("tenant_id")
    return requested


def assert_ticket_visible(user: dict[str, Any], ticket: dict[str, Any]) -> None:
    if user["role"] == UserRole.TENANT_USER and ticket["tenant_id"] != user.get("tenant_id"):
        raise NotFoundError("Ticket not found")


async def verify_webhook_token(x_webhook_token: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if not x_webhook_token or x_webhook_token != settings.webhook_token:
        raise UnauthorizedError("Invalid webhook token")
