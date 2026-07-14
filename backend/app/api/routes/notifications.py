from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep
from app.application.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(db: DbDep, user: CurrentUser):
    service = NotificationService(db)
    return {
        "items": await service.list_for(user["role"], user.get("tenant_id")),
        "unread": await service.unread_count(user["role"], user.get("tenant_id")),
    }


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(notification_id: str, db: DbDep, user: CurrentUser):
    await NotificationService(db).mark_read(notification_id)


@router.post("/read-all", status_code=204)
async def mark_all_read(db: DbDep, user: CurrentUser):
    await NotificationService(db).mark_all_read(user["role"], user.get("tenant_id"))
