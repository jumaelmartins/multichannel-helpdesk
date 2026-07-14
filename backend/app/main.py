from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    auth,
    bot,
    contacts,
    dashboard,
    demo,
    health,
    notifications,
    tenants,
    tickets,
    webhooks,
)
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.infra.database.mongodb import close_client, ensure_indexes, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await ensure_indexes(get_db())
    yield
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "A multichannel helpdesk API built with FastAPI and MongoDB. "
            "Supports ticket management, tenant-based support, message history, "
            "SLA tracking, webhook-based integrations and bot commands."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(health.router)
    for router in (
        auth.router,
        tenants.router,
        contacts.router,
        tickets.router,
        dashboard.router,
        webhooks.router,
        bot.router,
        notifications.router,
        demo.router,
    ):
        app.include_router(router, prefix="/api")

    return app


app = create_app()
