from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbDep, require_roles
from app.api.schemas.tenant import TenantCreateRequest, TenantUpdateRequest
from app.application.services.tenant_service import TenantService
from app.core.exceptions import ForbiddenError
from app.domain.enums import UserRole

router = APIRouter(prefix="/tenants", tags=["tenants"])

admin_only = Depends(require_roles(UserRole.ADMIN))
internal = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT, UserRole.VIEWER))


@router.post("", status_code=201, dependencies=[admin_only])
async def create_tenant(body: TenantCreateRequest, db: DbDep):
    return await TenantService(db).create(body.model_dump())


@router.get("", dependencies=[internal])
async def list_tenants(db: DbDep):
    return await TenantService(db).list()


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str, db: DbDep, user: CurrentUser):
    if user["role"] == UserRole.TENANT_USER and user.get("tenant_id") != tenant_id:
        raise ForbiddenError("Cannot access another tenant")
    return await TenantService(db).get(tenant_id)


@router.patch("/{tenant_id}", dependencies=[admin_only])
async def update_tenant(tenant_id: str, body: TenantUpdateRequest, db: DbDep):
    return await TenantService(db).update(tenant_id, body.model_dump(exclude_none=True))


@router.delete("/{tenant_id}", status_code=204, dependencies=[admin_only])
async def delete_tenant(tenant_id: str, db: DbDep):
    await TenantService(db).delete(tenant_id)
