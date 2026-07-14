from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.application.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbDep):
    return await AuthService(db).login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbDep):
    return await AuthService(db).refresh(body.refresh_token)


@router.get("/me")
async def me(user: CurrentUser):
    return {k: v for k, v in user.items() if k != "password_hash"}
