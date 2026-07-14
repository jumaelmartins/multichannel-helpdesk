from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import DbDep, verify_webhook_token
from app.application.services.webhook_service import WebhookService
from app.infra.channels import generic, telegram, whatsapp

router = APIRouter(
    prefix="/webhooks", tags=["webhooks"], dependencies=[Depends(verify_webhook_token)]
)


@router.post("/generic", status_code=202)
async def generic_webhook(payload: dict[str, Any], db: DbDep):
    return await WebhookService(db).process_inbound(generic.normalize(payload), payload)


@router.post("/whatsapp", status_code=202)
async def whatsapp_webhook(payload: dict[str, Any], db: DbDep):
    return await WebhookService(db).process_inbound(whatsapp.normalize(payload), payload)


@router.post("/telegram", status_code=202)
async def telegram_webhook(payload: dict[str, Any], db: DbDep):
    return await WebhookService(db).process_inbound(telegram.normalize(payload), payload)
