from fastapi import APIRouter, Depends

from app.api.deps import DbDep, require_roles
from app.domain.enums import UserRole
from app.infra.database.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)


@router.get("")
async def list_internal_users(db: DbDep):
    """List internal users (admins and agents) — used for ticket assignment."""
    users = await UserRepository(db).find(
        {"role": {"$in": ["admin", "agent"]}}, sort=[("name", 1)], limit=200
    )
    return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
