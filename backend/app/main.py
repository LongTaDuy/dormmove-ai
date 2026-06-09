"""DormMove AI FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router as api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Agentic move-in planning assistant for college students.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "version": __version__,
            "docs": "/docs",
        }

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "env": settings.app_env,
            "model_provider": settings.model_provider,
        }

    return app


app = create_app()
