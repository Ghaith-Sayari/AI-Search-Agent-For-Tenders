"""System endpoints: health of services and cost metrics."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from api.schemas.system import AgentsStatusResponse, CostByStage, CostMetrics
from api.services.system_service import SystemServiceLayer

router = APIRouter(prefix="/v1", tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/agents/status", response_model=AgentsStatusResponse)
async def get_agents_status() -> AgentsStatusResponse:
    service = SystemServiceLayer()
    return service.get_agents_status()


@router.get("/metrics/cost", response_model=CostMetrics)
async def get_cost_metrics(days: int = Query(default=7, ge=1, le=365)) -> CostMetrics:
    service = SystemServiceLayer()
    try:
        return service.get_cost_metrics(days=days)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to compute cost metrics; returning safe fallback. Error: %s", exc)
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=max(1, days))
        return CostMetrics(
            periodStart=period_start.isoformat(),
            periodEnd=now.isoformat(),
            llmCalls=0,
            promptTokens=0,
            completionTokens=0,
            estimatedCostUsd=0.0,
            byStage=[
                CostByStage(stage="GATEKEEPER", llmCalls=0, promptTokens=0, completionTokens=0, estimatedCostUsd=0.0),
                CostByStage(stage="OPPORTUNITY_ANALYSIS", llmCalls=0, promptTokens=0, completionTokens=0, estimatedCostUsd=0.0),
            ],
        )
