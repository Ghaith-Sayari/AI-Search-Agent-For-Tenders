"""Data access for review queue endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db.client import get_client


class ReviewRepository:
    def __init__(self) -> None:
        self.client = get_client()

    def list_gatekeeper_needs_review(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = (
            self.client.table("gatekeeper_decisions")
            .select("*")
            .eq("status", "needs_review")
            .order("processed_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
        return rows

    def get_raw_by_staging_id(self, staging_tender_id: str | None) -> dict[str, Any] | None:
        if not staging_tender_id:
            return None
        rows = (
            self.client.table("raw_tender_staging")
            .select("*")
            .eq("id", staging_tender_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def list_analysis_reviews(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = (
            self.client.table("analyzed_tender")
            .select("*")
            .eq("decision", "review")
            .order("processed_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
        return rows

    def resolve_gatekeeper(self, decision_id: str, *, action: str, actor: str, reason: str) -> dict[str, Any] | None:
        new_status = {
            "APPROVE": "approved",
            "REJECT": "rejected",
            "SEND_BACK": "needs_review",
        }.get(action, "needs_review")

        existing = (
            self.client.table("gatekeeper_decisions")
            .select("*")
            .eq("id", decision_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not existing:
            return None
        row = existing[0]
        note = f"[HITL:{action} by {actor}] {reason}".strip()
        decision_reason = str(row.get("decision_reason") or "")
        if note:
            decision_reason = f"{decision_reason}\n{note}".strip()

        updated = (
            self.client.table("gatekeeper_decisions")
            .update({"status": new_status, "decision_reason": decision_reason})
            .eq("id", decision_id)
            .execute()
            .data
            or []
        )
        return updated[0] if updated else None

    def resolve_analysis(self, analyzed_id: str, *, action: str, actor: str, reason: str) -> dict[str, Any] | None:
        new_decision = {
            "APPROVE": "pursue",
            "REJECT": "reject",
            "SEND_BACK": "review",
        }.get(action, "review")

        existing = (
            self.client.table("analyzed_tender")
            .select("*")
            .eq("id", analyzed_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not existing:
            return None
        row = existing[0]
        note = f"[HITL:{action} by {actor}] {reason}".strip()
        decision_reason = str(row.get("decision_reason") or "")
        if note:
            decision_reason = f"{decision_reason}\n{note}".strip()

        updated = (
            self.client.table("analyzed_tender")
            .update(
                {
                    "decision": new_decision,
                    "decision_reason": decision_reason,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", analyzed_id)
            .execute()
            .data
            or []
        )
        return updated[0] if updated else None
