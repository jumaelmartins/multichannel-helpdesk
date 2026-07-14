from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import UserRole


class User(BaseModel):
    id: str
    name: str
    email: str
    password_hash: str
    role: UserRole
    tenant_id: str | None = None
    created_at: datetime
    updated_at: datetime
