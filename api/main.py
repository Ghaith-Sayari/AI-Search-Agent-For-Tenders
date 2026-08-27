"""FastAPI application bootstrap for TenderIntel backend."""

from __future__ import annotations

import importlib
import logging
import os
import threading
from typing import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.services.offer_notification_service import OfferNotificationService

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

    @app.on_event("startup")
    async def _start_offer_notification_worker() -> None:
        service = OfferNotificationService()
        if not service.is_enabled():
            logger.info("Offer notification worker disabled by configuration.")
            return

        stop_event = threading.Event()
        interval_seconds = max(10, int(os.getenv("OFFER_EMAIL_POLL_INTERVAL_SECONDS", "60")))

        def _worker_loop() -> None:
            logger.info("Offer notification worker started (poll interval=%ss).", interval_seconds)
            while not stop_event.is_set():
                try:
                    service.process_pending_notifications()
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Offer notification worker iteration failed: %s", exc)
                stop_event.wait(interval_seconds)
            logger.info("Offer notification worker stopped.")

        worker = threading.Thread(
            target=_worker_loop,
            name="offer-notification-worker",
            daemon=True,
        )
        worker.start()
        app.state.offer_notification_worker = {
            "thread": worker,
            "stop_event": stop_event,
        }

    @app.on_event("shutdown")
    async def _stop_offer_notification_worker() -> None:
        worker_state = getattr(app.state, "offer_notification_worker", None)
        if not worker_state:
            return
        stop_event = worker_state.get("stop_event")
        worker = worker_state.get("thread")
        if stop_event:
            stop_event.set()
        if worker and worker.is_alive():
            worker.join(timeout=5)

    return app


app = create_app()
