from fastapi import APIRouter

from app.api.deps import DbDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: DbDep):
    await db.command("ping")
    return {"status": "ready"}
