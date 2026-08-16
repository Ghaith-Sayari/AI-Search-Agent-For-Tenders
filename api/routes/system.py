"""System endpoints: health of services and cost metrics."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.system import AgentsStatusResponse, CostMetrics
from api.services.system_service import SystemServiceLayer

router = APIRouter(prefix="/v1", tags=["system"])


@router.get("/agents/status", response_model=AgentsStatusResponse)
async def get_agents_status() -> AgentsStatusResponse:
    service = SystemServiceLayer()
    return service.get_agents_status()


@router.get("/metrics/cost", response_model=CostMetrics)
async def get_cost_metrics(days: int = Query(default=7, ge=1, le=365)) -> CostMetrics:
    service = SystemServiceLayer()
    return service.get_cost_metrics(days=days)
