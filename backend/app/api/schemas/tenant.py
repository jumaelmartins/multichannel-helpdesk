from pydantic import BaseModel

from app.domain.enums import TenantStatus


class TenantCreateRequest(BaseModel):
    name: str
    slug: str | None = None
    document: str | None = None
    status: TenantStatus = TenantStatus.ACTIVE


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    document: str | None = None
    status: TenantStatus | None = None
