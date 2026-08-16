"""Service layer for pipeline run lifecycle endpoints."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from api.schemas.runs import CreateRunRequest, PipelineRun, PipelineStage

_RUNS: dict[str, PipelineRun] = {}
_LOCK = Lock()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_stages() -> list[PipelineStage]:
    return [
        PipelineStage(stage="INGESTION", label="Ingestion", status="PENDING"),
        PipelineStage(stage="NORMALIZATION", label="Normalization", status="PENDING"),
        PipelineStage(stage="GATEKEEPER", label="Gatekeeper", status="PENDING"),
        PipelineStage(stage="PRODUCTION", label="Production publish", status="PENDING"),
        PipelineStage(stage="OPPORTUNITY_ANALYSIS", label="Opportunity analysis", status="PENDING"),
        PipelineStage(stage="REVIEW", label="Review routing", status="PENDING"),
        PipelineStage(stage="COMPLETED", label="Completed", status="PENDING"),
    ]


def list_runs() -> list[PipelineRun]:
    with _LOCK:
        runs = list(_RUNS.values())
    runs.sort(key=lambda r: r.startedAt, reverse=True)
    return runs


def get_run(run_id: str) -> PipelineRun | None:
    with _LOCK:
        run = _RUNS.get(run_id)
    return deepcopy(run) if run else None


def create_run(request: CreateRunRequest) -> PipelineRun:
    run = PipelineRun(
        id=str(uuid4()),
        triggeredBy=request.triggerName or "api",
        startedAt=_utc_iso(),
        currentStage="INGESTION",
        status="QUEUED",
        stages=_base_stages(),
    )
    with _LOCK:
        _RUNS[run.id] = run
    return deepcopy(run)


def execute_run(run_id: str, request: CreateRunRequest) -> None:
    """Execute one run in background.

    Currently this calls orchestration service when available and maps summary
    into the frontend-facing run model.
    """
    with _LOCK:
        run = _RUNS.get(run_id)
        if not run:
            return
        run.status = "RUNNING"
        run.currentStage = "INGESTION"
        run.stages[0].status = "RUNNING"

    try:
        from orchestration.langgraph.run_service import RunRequest, run_and_get_summary

        req = RunRequest(
            mode=request.mode,
            profile_id=request.profileId,
            limit=request.limit,
            run_id=run_id,
        )
        summary: dict[str, Any] = run_and_get_summary(req)

        with _LOCK:
            run = _RUNS.get(run_id)
            if not run:
                return

            # Stage snapshots (coarse mapping for now)
            run.stages[0].status = "COMPLETED"
            run.stages[1].status = "COMPLETED"
            run.stages[2].status = "COMPLETED"
            run.stages[3].status = "COMPLETED"
            run.stages[4].status = "COMPLETED"
            run.stages[5].status = "COMPLETED"
            run.stages[6].status = "COMPLETED"
            run.currentStage = "COMPLETED"

            gk = summary.get("gatekeeper", {})
            an = summary.get("analysis", {})
            cost = summary.get("cost", {})

            run.processedCount = int(gk.get("processed", 0)) + int(an.get("processed", 0))
            run.approvedCount = int(gk.get("approved", 0))
            run.reviewCount = int(gk.get("needs_review", 0)) + int(an.get("review", 0))
            run.failedCount = int(gk.get("failed", 0)) + int(an.get("failed", 0))
            run.llmCallsCount = int(cost.get("llm_calls", 0))
            run.status = "COMPLETED"
            run.completedAt = _utc_iso()

            started = datetime.fromisoformat(run.startedAt)
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            completed = datetime.fromisoformat(run.completedAt)
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)
            run.durationSeconds = max(0.0, (completed - started).total_seconds())
    except Exception as exc:  # noqa: BLE001
        with _LOCK:
            run = _RUNS.get(run_id)
            if not run:
                return
            run.status = "FAILED"
            run.currentStage = "COMPLETED"
            run.stages[6].status = "FAILED"
            run.stages[6].errorsCount = 1
            run.stages[6].details = {"error": str(exc)}
            run.completedAt = _utc_iso()

            started = datetime.fromisoformat(run.startedAt)
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            completed = datetime.fromisoformat(run.completedAt)
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)
            run.durationSeconds = max(0.0, (completed - started).total_seconds())
