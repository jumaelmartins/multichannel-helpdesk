from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep, scoped_tenant_id
from app.application.services.ticket_service import TicketService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(db: DbDep, user: CurrentUser):
    return await TicketService(db).dashboard_stats(tenant_id=scoped_tenant_id(user))
