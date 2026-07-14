import re
import unicodedata
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import ConflictError, NotFoundError
from app.infra.database.repositories.tenant_repository import TenantRepository


def slugify(value: str) -> str:
    value = "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "tenant"


class TenantService:
    def __init__(self, db: AsyncDatabase):
        self.tenants = TenantRepository(db)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        slug = data.get("slug") or slugify(data["name"])
        if await self.tenants.get_by_slug(slug):
            raise ConflictError(f"Tenant slug already exists: {slug}")
        return await self.tenants.insert(
            {
                "name": data["name"],
                "slug": slug,
                "document": data.get("document"),
                "status": data.get("status", "active"),
            }
        )

    async def list(self) -> list[dict[str, Any]]:
        return await self.tenants.find(sort=[("name", 1)], limit=200)

    async def get(self, tenant_id: str) -> dict[str, Any]:
        tenant = await self.tenants.get(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found")
        return tenant

    async def update(self, tenant_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        await self.get(tenant_id)
        if "slug" in updates and updates["slug"]:
            existing = await self.tenants.get_by_slug(updates["slug"])
            if existing and existing["id"] != tenant_id:
                raise ConflictError(f"Tenant slug already exists: {updates['slug']}")
        tenant = await self.tenants.update(tenant_id, updates)
        return tenant

    async def delete(self, tenant_id: str) -> None:
        await self.get(tenant_id)
        await self.tenants.delete(tenant_id)
