from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbDep, require_roles
from app.api.schemas.bot import BotCommandRequest, BotCommandResponse
from app.application.services.bot_service import BotService
from app.domain.enums import UserRole

router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))],
)


@router.post("/command", response_model=BotCommandResponse)
async def run_command(body: BotCommandRequest, db: DbDep, user: CurrentUser):
    reply = await BotService(db).execute(body.command, user)
    return {"reply": reply}
