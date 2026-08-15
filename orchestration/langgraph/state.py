"""LangGraph shared state contract for orchestration runs.

This module intentionally contains only data contracts + lightweight helpers.
Business logic should stay in node modules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from operator import add
from typing import Annotated, Any, Literal, TypedDict


TerminalStatus = Literal["running", "completed", "failed", "cancelled"]
ReviewType = Literal["gatekeeper", "analysis"]


class RunState(TypedDict):
    run_id: str
    mode: str
    profile_id: str | None
    started_at: str
    policy_version: str
    gatekeeper_agent_version: str
    analysis_agent_version: str


class ScopeState(TypedDict):
    limit: int | None
    sources: list[str]
    since: str | None
    dry_run: bool


class GatekeeperCounters(TypedDict):
    fetched: int
    skipped: int
    processed: int
    approved: int
    needs_review: int
    rejected: int
    expired: int
    failed: int
    dlq: int


class AnalysisCounters(TypedDict):
    fetched: int
    skipped: int
    processed: int
    pursue: int
    review: int
    reject: int
    failed: int


class CurrentItemState(TypedDict):
    unique_key: str | None
    staging_tender_id: str | None
    production_tender_id: str | None
    analyzed_tender_id: str | None


class ErrorRecord(TypedDict):
    stage: str
    unique_key: str | None
    error_type: str
    message: str
    retry_count: int
    occurred_at: str


class ReviewItem(TypedDict):
    review_type: ReviewType
    unique_key: str
    entity_id: str | None
    reason: str
    confidence_score: float | None
    review_id: str | None


class CostState(TypedDict):
    llm_calls: int
    retry_attempts: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


class StatusState(TypedDict):
    current_node: str
    terminal_status: TerminalStatus
    last_error: str | None


class ArtifactsState(TypedDict):
    trace_ids: list[str]
    summary: dict[str, Any]


class GraphState(TypedDict):
    run: RunState
    scope: ScopeState
    gatekeeper: GatekeeperCounters
    analysis: AnalysisCounters
    current: CurrentItemState
    errors: Annotated[list[ErrorRecord], add]
    review_queue: Annotated[list[ReviewItem], add]
    cost: CostState
    status: StatusState
    artifacts: ArtifactsState


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_initial_state(
    *,
    run_id: str,
    mode: str = "full",
    profile_id: str | None = None,
    limit: int | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    dry_run: bool = False,
    policy_version: str = "1.0",
    gatekeeper_agent_version: str = "1.0",
    analysis_agent_version: str = "1.0",
) -> GraphState:
    """Create a fully-initialized graph state."""

    return {
        "run": {
            "run_id": run_id,
            "mode": mode,
            "profile_id": profile_id,
            "started_at": _utc_now_iso(),
            "policy_version": policy_version,
            "gatekeeper_agent_version": gatekeeper_agent_version,
            "analysis_agent_version": analysis_agent_version,
        },
        "scope": {
            "limit": limit,
            "sources": sources or [],
            "since": since,
            "dry_run": dry_run,
        },
        "gatekeeper": {
            "fetched": 0,
            "skipped": 0,
            "processed": 0,
            "approved": 0,
            "needs_review": 0,
            "rejected": 0,
            "expired": 0,
            "failed": 0,
            "dlq": 0,
        },
        "analysis": {
            "fetched": 0,
            "skipped": 0,
            "processed": 0,
            "pursue": 0,
            "review": 0,
            "reject": 0,
            "failed": 0,
        },
        "current": {
            "unique_key": None,
            "staging_tender_id": None,
            "production_tender_id": None,
            "analyzed_tender_id": None,
        },
        "errors": [],
        "review_queue": [],
        "cost": {
            "llm_calls": 0,
            "retry_attempts": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
        "status": {
            "current_node": "start_run",
            "terminal_status": "running",
            "last_error": None,
        },
        "artifacts": {
            "trace_ids": [],
            "summary": {},
        },
    }


def make_error(
    *,
    stage: str,
    message: str,
    error_type: str = "RuntimeError",
    unique_key: str | None = None,
    retry_count: int = 0,
) -> ErrorRecord:
    """Create a normalized error payload for state aggregation."""

    return {
        "stage": stage,
        "unique_key": unique_key,
        "error_type": error_type,
        "message": message,
        "retry_count": retry_count,
        "occurred_at": _utc_now_iso(),
    }
