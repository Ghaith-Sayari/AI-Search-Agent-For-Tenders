"""FastAPI application bootstrap for TenderIntel backend."""

from __future__ import annotations

import importlib
import logging
from typing import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def _safe_include_routers(app: FastAPI, routers: Iterable[tuple[str, str]]) -> None:
    """Import routers dynamically and include them when available.

    This keeps startup resilient while route modules are still being implemented.
    """
    for module_path, router_attr in routers:
        try:
            module = importlib.import_module(module_path)
            router = getattr(module, router_attr)
            app.include_router(router)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Router not loaded: %s.%s (%s)", module_path, router_attr, exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title="TenderIntel API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # TODO: tighten this in production to explicit frontend origins only.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    _safe_include_routers(
        app,
        [
            ("api.routes.runs", "router"),
            ("api.routes.opportunities", "router"),
            ("api.routes.reviews", "router"),
            ("api.routes.proposals", "router"),
            ("api.routes.system", "router"),
            ("api.routes.company_profile", "router"),
        ],
    )

    return app


app = create_app()
