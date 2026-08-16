"""Service layer for review queue endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from api.mappers.review_mapper import (
    build_resolution_audit,
    map_analysis_review,
    map_gatekeeper_review,
)
from api.repositories.review_repository import ReviewRepository
from api.schemas.reviews import ResolveReviewRequest, ReviewItem

_RESOLVED: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


class ReviewService:
    def __init__(self, repository: ReviewRepository | None = None) -> None:
        self.repository = repository or ReviewRepository()

    def list_reviews(self) -> list[ReviewItem]:
        items: list[ReviewItem] = []

        for row in self.repository.list_gatekeeper_needs_review():
            raw = self.repository.get_raw_by_staging_id(str(row.get("staging_tender_id")) if row.get("staging_tender_id") else None)
            item = map_gatekeeper_review(row, raw)
            resolved = _RESOLVED.get(item.id)
            if resolved:
                item.status = resolved["status"]
                item.resolvedAt = resolved.get("resolvedAt")
                item.resolvedBy = resolved.get("resolvedBy")
                item.overrideReason = resolved.get("overrideReason")
                item.auditTrail = resolved.get("auditTrail", [])
            items.append(item)

        for row in self.repository.list_analysis_reviews():
            item = map_analysis_review(row)
            resolved = _RESOLVED.get(item.id)
            if resolved:
                item.status = resolved["status"]
                item.resolvedAt = resolved.get("resolvedAt")
                item.resolvedBy = resolved.get("resolvedBy")
                item.overrideReason = resolved.get("overrideReason")
                item.auditTrail = resolved.get("auditTrail", [])
            items.append(item)

        # show open first, then by priority
        order = {"OPEN": 0, "RESOLVED_SENT_BACK": 1, "RESOLVED_APPROVED": 2, "RESOLVED_REJECTED": 3}
        prio = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        items.sort(key=lambda x: (order.get(x.status, 99), prio.get(x.priority, 99)))
        return items

    def resolve_review(self, review_id: str, payload: ResolveReviewRequest) -> ReviewItem | None:
        try:
            review_type, db_id = review_id.split(":", 1)
        except ValueError:
            return None

        review_type = review_type.upper()
        action = payload.action
        actor = payload.actorName
        reason = payload.overrideReason

        if review_type == "GATEKEEPER":
            updated = self.repository.resolve_gatekeeper(db_id, action=action, actor=actor, reason=reason)
            if not updated:
                return None
            raw = self.repository.get_raw_by_staging_id(
                str(updated.get("staging_tender_id")) if updated.get("staging_tender_id") else None
            )
            item = map_gatekeeper_review(updated, raw)
        elif review_type == "OPPORTUNITY_ANALYSIS":
            updated = self.repository.resolve_analysis(db_id, action=action, actor=actor, reason=reason)
            if not updated:
                return None
            item = map_analysis_review(updated)
        else:
            return None

        status_map = {
            "APPROVE": "RESOLVED_APPROVED",
            "REJECT": "RESOLVED_REJECTED",
            "SEND_BACK": "RESOLVED_SENT_BACK",
        }
        resolved_status = status_map.get(action, "RESOLVED_SENT_BACK")
        resolved_at = datetime.now(timezone.utc).isoformat()
        audit = build_resolution_audit(action=action, actor=actor, notes=reason)

        item.status = resolved_status
        item.resolvedAt = resolved_at
        item.resolvedBy = actor
        item.overrideReason = reason
        item.auditTrail = audit

        with _LOCK:
            _RESOLVED[item.id] = {
                "status": item.status,
                "resolvedAt": item.resolvedAt,
                "resolvedBy": item.resolvedBy,
                "overrideReason": item.overrideReason,
                "auditTrail": item.auditTrail,
            }
        return item
