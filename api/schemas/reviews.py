"""Schemas for review queue endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DecisionStatus = Literal["GOOD_FIT", "NEEDS_REVIEW", "NOT_FIT", "FAILED"]
ReviewType = Literal["GATEKEEPER", "OPPORTUNITY_ANALYSIS"]
Priority = Literal["HIGH", "MEDIUM", "LOW"]
ReviewStatus = Literal["OPEN", "RESOLVED_APPROVED", "RESOLVED_REJECTED", "RESOLVED_SENT_BACK"]
ResolveAction = Literal["APPROVE", "REJECT", "SEND_BACK"]


class ReviewAuditEntry(BaseModel):
    timestamp: str
    action: str
    actor: str
    notes: str = ""


class ReviewItem(BaseModel):
    id: str
    opportunityId: str
    opportunityTitle: str
    country: str = ""
    source: str = ""
    reviewType: ReviewType
    aiDecision: DecisionStatus = "NEEDS_REVIEW"
    score: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    priority: Priority = "MEDIUM"
    assignee: str | None = None
    status: ReviewStatus = "OPEN"
    resolvedAt: str | None = None
    resolvedBy: str | None = None
    overrideReason: str | None = None
    auditTrail: list[ReviewAuditEntry] = Field(default_factory=list)


class ResolveReviewRequest(BaseModel):
    action: ResolveAction
    overrideReason: str = ""
    actorName: str
