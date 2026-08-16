"""Opportunity API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas.opportunities import Opportunity
from api.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/v1/opportunities", tags=["opportunities"])


@router.get("", response_model=list[Opportunity])
async def list_opportunities(
    search: str | None = Query(default=None),
    country: str | None = Query(default=None),
    source: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    minScore: float | None = Query(default=None, ge=0, le=100),
    maxScore: float | None = Query(default=None, ge=0, le=100),
    sortBy: str = Query(default="lastAnalyzedAt"),
    sortOrder: str = Query(default="desc", pattern="^(asc|desc|ASC|DESC)$"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Opportunity]:
    service = OpportunityService()
    decision_map = {
        "GOOD_FIT": "pursue",
        "NEEDS_REVIEW": "review",
        "NOT_FIT": "reject",
        "FAILED": "failed",
    }
    internal_decision = decision_map.get(decision, decision)
    return service.list_opportunities(
        search=search,
        country=country,
        source=source,
        decision=internal_decision,
        min_score=minScore,
        max_score=maxScore,
        sort_by=sortBy,
        sort_order=sortOrder,
        limit=limit,
    )


@router.get("/{opportunity_id}", response_model=Opportunity)
async def get_opportunity(opportunity_id: str) -> Opportunity:
    service = OpportunityService()
    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail=f"Opportunity '{opportunity_id}' not found")
    return opportunity
