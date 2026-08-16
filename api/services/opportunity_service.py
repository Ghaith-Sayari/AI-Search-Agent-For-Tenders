"""Service layer for opportunities endpoints."""

from __future__ import annotations

from api.mappers.opportunity_mapper import to_opportunity
from api.repositories.opportunity_repository import OpportunityRepository
from api.schemas.opportunities import Opportunity


class OpportunityService:
    def __init__(self, repository: OpportunityRepository | None = None) -> None:
        self.repository = repository or OpportunityRepository()

    def list_opportunities(
        self,
        *,
        search: str | None = None,
        country: str | None = None,
        source: str | None = None,
        decision: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        sort_by: str = "processed_at",
        sort_order: str = "desc",
        limit: int = 100,
    ) -> list[Opportunity]:
        rows = self.repository.list_analyzed(
            search=search,
            country=country,
            source=source,
            decision=decision,
            min_score=min_score,
            max_score=max_score,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )
        production_ids = [str(r.get("production_tender_id")) for r in rows if r.get("production_tender_id")]
        production_map = self.repository.get_production_rows(production_ids)
        return [
            to_opportunity(row, production_map.get(str(row.get("production_tender_id"))))
            for row in rows
        ]

    def get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        analyzed = self.repository.get_analyzed_by_id(opportunity_id)
        if not analyzed:
            return None
        production = self.repository.get_production_by_id(analyzed.get("production_tender_id"))
        return to_opportunity(analyzed, production)
