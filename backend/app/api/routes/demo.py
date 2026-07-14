"""Demo-only endpoints (public repository). Disabled when DEMO_MODE=false."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import DbDep
from app.application.services.seed_service import SeedService
from app.application.services.webhook_service import WebhookService
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError
from app.infra.channels import whatsapp


def require_demo_mode() -> None:
    if not get_settings().demo_mode:
        raise ForbiddenError("Demo endpoints are disabled")


router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(require_demo_mode)])


class SimulateWhatsAppRequest(BaseModel):
    tenant_slug: str | None = None
    name: str = "Carlos Silva"
    phone: str = "+5571999999999"
    message: str = "Olá, estou com um problema no sistema."
    title: str | None = None


@router.post("/seed")
async def seed(db: DbDep) -> dict[str, Any]:
    return await SeedService(db).seed()


@router.post("/reset")
async def reset(db: DbDep) -> dict[str, Any]:
    return await SeedService(db).reset()


@router.post("/simulate-whatsapp-message")
async def simulate_whatsapp_message(body: SimulateWhatsAppRequest, db: DbDep) -> dict[str, Any]:
    payload = {
        "id": f"wamid.demo-{uuid.uuid4().hex[:12]}",
        "from": body.phone,
        "name": body.name,
        "message": body.message,
        "tenant_slug": body.tenant_slug,
    }
    if body.title:
        payload["title"] = body.title
    result = await WebhookService(db).process_inbound(whatsapp.normalize(payload), payload)
    return {"simulated_payload": payload, **result}
