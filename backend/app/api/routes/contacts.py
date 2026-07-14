from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbDep, require_roles, scoped_tenant_id
from app.api.schemas.contact import ContactCreateRequest, ContactUpdateRequest
from app.application.services.contact_service import ContactService
from app.domain.enums import UserRole

router = APIRouter(prefix="/contacts", tags=["contacts"])

internal = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))


@router.post("", status_code=201, dependencies=[internal])
async def create_contact(body: ContactCreateRequest, db: DbDep):
    return await ContactService(db).create(body.model_dump())


@router.get("")
async def list_contacts(db: DbDep, user: CurrentUser, tenant_id: str | None = None):
    return await ContactService(db).list(scoped_tenant_id(user, tenant_id))


@router.get("/{contact_id}", dependencies=[internal])
async def get_contact(contact_id: str, db: DbDep):
    return await ContactService(db).get(contact_id)


@router.patch("/{contact_id}", dependencies=[internal])
async def update_contact(contact_id: str, body: ContactUpdateRequest, db: DbDep):
    return await ContactService(db).update(contact_id, body.model_dump(exclude_none=True))
