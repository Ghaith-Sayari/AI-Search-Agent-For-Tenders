"""Shared LangGraph nodes/helpers used by multiple orchestration flows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from orchestration.langgraph.state import GraphState, make_error


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(dt_value: str | None) -> datetime | None:
    if not dt_value:
        return None
    try:
        return datetime.fromisoformat(dt_value)
    except ValueError:
        return None


def start_run(state: GraphState) -> dict[str, Any]:
    """Initialize run-level metadata once execution enters the graph."""
    status = dict(state.get("status", {}))
    status["current_node"] = "start_run"
    status["terminal_status"] = "running"
    status["last_error"] = None

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    summary["run_id"] = state.get("run", {}).get("run_id")
    summary["mode"] = state.get("run", {}).get("mode")
    summary["profile_id"] = state.get("run", {}).get("profile_id")
    summary["started_at"] = state.get("run", {}).get("started_at")
    artifacts["summary"] = summary

    return {
        "status": status,
        "artifacts": artifacts,
    }


def set_current_node(state: GraphState, node_name: str) -> dict[str, Any]:
    """Set the active node name for progress/observability."""
    status = dict(state.get("status", {}))
    status["current_node"] = node_name
    return {"status": status}


def record_error(
    state: GraphState,
    *,
    stage: str,
    message: str,
    unique_key: str | None = None,
    retry_count: int = 0,
    error_type: str = "RuntimeError",
    mark_run_failed: bool = False,
) -> dict[str, Any]:
    """Record a normalized error and update run status."""
    error_item = make_error(
        stage=stage,
        message=message,
        error_type=error_type,
        unique_key=unique_key,
        retry_count=retry_count,
    )

    status = dict(state.get("status", {}))
    status["last_error"] = f"{stage}: {message}"
    if mark_run_failed:
        status["terminal_status"] = "failed"

    # `errors` uses reducer semantics in GraphState, so return only new item.
    return {
        "errors": [error_item],
        "status": status,
    }


def finalize_run(
    state: GraphState,
    *,
    terminal_status: Literal["completed", "failed", "cancelled"] = "completed",
) -> dict[str, Any]:
    """Compute and persist final summary block for the run."""
    run = state.get("run", {})
    gatekeeper = state.get("gatekeeper", {})
    analysis = state.get("analysis", {})
    cost = state.get("cost", {})

    started_at_dt = _parse_iso(run.get("started_at"))
    finished_at_dt = _now_utc()

    duration_seconds: float | None = None
    if started_at_dt is not None:
        # If parsed datetime is naive, assume UTC.
        if started_at_dt.tzinfo is None:
            started_at_dt = started_at_dt.replace(tzinfo=timezone.utc)
        duration_seconds = max(0.0, (finished_at_dt - started_at_dt).total_seconds())

    errors = list(state.get("errors", []))
    errors_count = len(errors)
    severe_prefixes = (
        "gatekeeper.persist_decision",
        "gatekeeper.classify",
        "gatekeeper.publish",
        "analysis.llm_judgment",
        "analysis.persist",
    )
    has_severe_errors = any(
        str(err.get("stage") or "").startswith(severe_prefixes)
        for err in errors
        if isinstance(err, dict)
    )
    computed_terminal_status = (
        "failed" if terminal_status == "completed" and has_severe_errors else terminal_status
    )

    summary = {
        "run_id": run.get("run_id"),
        "mode": run.get("mode"),
        "profile_id": run.get("profile_id"),
        "policy_version": run.get("policy_version"),
        "started_at": run.get("started_at"),
        "finished_at": finished_at_dt.isoformat(),
        "duration_seconds": duration_seconds,
        "terminal_status": computed_terminal_status,
        "had_errors": errors_count > 0,
        "has_severe_errors": has_severe_errors,
        "gatekeeper": {
            "fetched": gatekeeper.get("fetched", 0),
            "skipped": gatekeeper.get("skipped", 0),
            "processed": gatekeeper.get("processed", 0),
            "approved": gatekeeper.get("approved", 0),
            "needs_review": gatekeeper.get("needs_review", 0),
            "rejected": gatekeeper.get("rejected", 0),
            "expired": gatekeeper.get("expired", 0),
            "failed": gatekeeper.get("failed", 0),
            "dlq": gatekeeper.get("dlq", 0),
        },
        "analysis": {
            "fetched": analysis.get("fetched", 0),
            "skipped": analysis.get("skipped", 0),
            "processed": analysis.get("processed", 0),
            "pursue": analysis.get("pursue", 0),
            "review": analysis.get("review", 0),
            "reject": analysis.get("reject", 0),
            "failed": analysis.get("failed", 0),
        },
        "errors_count": errors_count,
        "review_items_count": len(state.get("review_queue", [])),
        "cost": {
            "llm_calls": cost.get("llm_calls", 0),
            "retry_attempts": cost.get("retry_attempts", 0),
            "prompt_tokens": cost.get("prompt_tokens", 0),
            "completion_tokens": cost.get("completion_tokens", 0),
            "estimated_cost_usd": cost.get("estimated_cost_usd", 0.0),
        },
    }

    status = dict(state.get("status", {}))
    status["current_node"] = "finalize_run"
    status["terminal_status"] = computed_terminal_status

    artifacts = dict(state.get("artifacts", {}))
    artifacts["summary"] = summary

    return {
        "status": status,
        "artifacts": artifacts,
    }
