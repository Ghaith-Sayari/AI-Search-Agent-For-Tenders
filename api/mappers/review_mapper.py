"""Mapper for review queue DTOs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.schemas.reviews import ReviewAuditEntry, ReviewItem


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _priority_from_confidence(conf_0_100: float) -> str:
    if conf_0_100 < 40:
        return "HIGH"
    if conf_0_100 < 70:
        return "MEDIUM"
    return "LOW"


def _map_ai_decision(decision: str | None) -> str:
    mapping = {
        "approved": "GOOD_FIT",
        "needs_review": "NEEDS_REVIEW",
        "rejected": "NOT_FIT",
        "expired": "NOT_FIT",
        "failed": "FAILED",
        "pursue": "GOOD_FIT",
        "review": "NEEDS_REVIEW",
        "reject": "NOT_FIT",
    }
    return mapping.get((decision or "").lower(), "NEEDS_REVIEW")


def map_gatekeeper_review(decision_row: dict[str, Any], raw_row: dict[str, Any] | None = None) -> ReviewItem:
    raw_row = raw_row or {}
    confidence = float(decision_row.get("confidence_score") or 0.0) * 100.0
    item = ReviewItem(
        id=f"GATEKEEPER:{decision_row.get('id')}",
        opportunityId=str(raw_row.get("id") or decision_row.get("staging_tender_id") or ""),
        opportunityTitle=str(raw_row.get("title") or decision_row.get("unique_key") or "Untitled"),
        country=str(raw_row.get("country") or ""),
        source=str(raw_row.get("source") or ""),
        reviewType="GATEKEEPER",
        aiDecision=_map_ai_decision(str(decision_row.get("status") or "")),
        score=0.0,
        confidence=confidence,
        reason=str(decision_row.get("decision_reason") or ""),
        priority=_priority_from_confidence(confidence),
        status="OPEN",
        auditTrail=[],
    )
    return item


def map_analysis_review(analyzed_row: dict[str, Any]) -> ReviewItem:
    confidence = float(analyzed_row.get("confidence_score") or 0.0) * 100.0
    score = float(analyzed_row.get("total_score") or 0.0)
    return ReviewItem(
        id=f"OPPORTUNITY_ANALYSIS:{analyzed_row.get('id')}",
        opportunityId=str(analyzed_row.get("production_tender_id") or analyzed_row.get("id") or ""),
        opportunityTitle=str(analyzed_row.get("title") or analyzed_row.get("unique_key") or "Untitled"),
        country=str(analyzed_row.get("country") or ""),
        source=str(analyzed_row.get("source") or ""),
        reviewType="OPPORTUNITY_ANALYSIS",
        aiDecision=_map_ai_decision(str(analyzed_row.get("decision") or "")),
        score=score,
        confidence=confidence,
        reason=str(analyzed_row.get("decision_reason") or ""),
        priority=_priority_from_confidence(confidence),
        status="OPEN",
        auditTrail=[],
    )


def build_resolution_audit(*, action: str, actor: str, notes: str) -> list[ReviewAuditEntry]:
    return [ReviewAuditEntry(timestamp=_iso_now(), action=action, actor=actor, notes=notes)]
