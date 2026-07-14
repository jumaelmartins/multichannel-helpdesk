from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import TenantStatus


class Tenant(BaseModel):
    id: str
    name: str
    slug: str
    document: str | None = None
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
