"""Data access for opportunities endpoints."""

from __future__ import annotations

from typing import Any

from db.client import get_client


class OpportunityRepository:
    def __init__(self) -> None:
        self.client = get_client()

    def list_analyzed(
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
    ) -> list[dict[str, Any]]:
        query = self.client.table("analyzed_tender").select("*")

        if search:
            like = f"%{search}%"
            query = query.or_(f"title.ilike.{like},decision_reason.ilike.{like}")
        if country:
            query = query.eq("country", country)
        if source:
            query = query.eq("source", source)
        if decision:
            query = query.eq("decision", decision)
        if min_score is not None:
            query = query.gte("total_score", min_score)
        if max_score is not None:
            query = query.lte("total_score", max_score)

        sort_field_map = {
            "overallScore": "total_score",
            "score": "total_score",
            "confidence": "confidence_score",
            "deadline": "deadline",
            "publishedDate": "created_at",
            "lastAnalyzedAt": "processed_at",
            "createdAt": "created_at",
            "processed_at": "processed_at",
        }
        order_field = sort_field_map.get(sort_by, "processed_at")
        desc = str(sort_order).lower() != "asc"
        query = query.order(order_field, desc=desc).limit(max(1, min(limit, 500)))
        return query.execute().data or []

    def get_analyzed_by_id(self, opportunity_id: str) -> dict[str, Any] | None:
        # Try analyzed_tender primary id first
        result = (
            self.client.table("analyzed_tender")
            .select("*")
            .eq("id", opportunity_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if result:
            return result[0]

        # Fallback by production_tender_id or unique_key for convenience
        result = (
            self.client.table("analyzed_tender")
            .select("*")
            .or_(f"production_tender_id.eq.{opportunity_id},unique_key.eq.{opportunity_id}")
            .order("processed_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return result[0] if result else None

    def get_production_rows(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        cleaned = [i for i in ids if i]
        if not cleaned:
            return {}
        rows = (
            self.client.table("production_tender")
            .select("*")
            .in_("id", cleaned)
            .execute()
            .data
            or []
        )
        return {str(r.get("id")): r for r in rows if r.get("id")}

    def get_production_by_id(self, production_tender_id: str | None) -> dict[str, Any] | None:
        if not production_tender_id:
            return None
        rows = (
            self.client.table("production_tender")
            .select("*")
            .eq("id", production_tender_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
