from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.app.db import ApiConfigError
from api.app.routes import copilot, health, metrics


def _client_origins() -> list[str]:
    raw_value = os.getenv("CLIENT_ORIGINS") or os.getenv("CLIENT_ORIGIN") or ""
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bike Store Analytics API",
        version="0.5.0",
        description="FastAPI service layer for Bike Store metrics and copilot templates.",
    )

    origins = _client_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(ApiConfigError)
    async def api_config_error_handler(_: Request, exc: ApiConfigError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(copilot.router)
    return app


app = create_app()
