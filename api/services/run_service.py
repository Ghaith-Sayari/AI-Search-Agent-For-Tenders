"""Service layer for pipeline run lifecycle endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from api.repositories.run_repository import RunRepository
from api.schemas.runs import CreateRunRequest, PipelineRun, PipelineStage


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_ingestion_error(exc: Exception) -> str:
    """Normalize scraper errors into actionable, non-empty messages."""
    base = str(exc).strip()
    if not base:
        base = f"{type(exc).__name__}: {repr(exc)}"

    lowered = base.lower()
    if "winerror 5" in lowered or "access is denied" in lowered or "accès refusé" in lowered:
        return (
            f"{base} (Playwright could not launch browser process. "
            "Check OS permissions/antivirus or run backend with proper rights.)"
        )
    return base


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


def _set_stage_status(
    run: PipelineRun,
    stage_name: str,
    status: str,
    *,
    details: dict[str, Any] | None = None,
) -> None:
    for st in run.stages:
        if st.stage == stage_name:
            st.status = status  # type: ignore[assignment]
            if details is not None:
                st.details = details
            return


def _ingest_from_scrapers(per_source_limit: int = 20) -> dict[str, Any]:
    """
    Run scraper ingestion inline for pipeline runs:
    - fetch from each discovered scraper
    - keep only first N items per scraper
    - normalize + load into raw_tender_staging directly
    """
    from db.loader import load_all
    from pipeline.normalizer import normalize_batch
    from scrapers.registry import discover_scrapers

    per_source_limit = max(1, int(per_source_limit))
    scrapers = discover_scrapers()
    stats: dict[str, Any] = {
        "scrapers": len(scrapers),
        "per_source_limit": per_source_limit,
        "fetched": 0,
        "normalized": 0,
        "dropped": 0,
        "errors": {},
        "sources": {},
    }

    for source_name, scraper in scrapers.items():
        try:
            raw = scraper.fetch() or []
            if not isinstance(raw, list):
                raw = []
            fetched_before_limit = len(raw)
            raw = raw[:per_source_limit]
            valid, dropped = normalize_batch(raw)
            if valid:
                load_all(valid)
            stats["fetched"] += len(raw)
            stats["normalized"] += len(valid)
            stats["dropped"] += int(dropped)
            stats["sources"][source_name] = {
                "fetched_before_limit": fetched_before_limit,
                "fetched": len(raw),
                "normalized": len(valid),
                "dropped": int(dropped),
                "error": "",
                "note": "no_items_returned_by_scraper" if fetched_before_limit == 0 else "",
            }
        except Exception as exc:  # noqa: BLE001
            err_msg = _format_ingestion_error(exc)
            stats["errors"][source_name] = err_msg
            stats["sources"][source_name] = {
                "fetched_before_limit": 0,
                "fetched": 0,
                "normalized": 0,
                "dropped": 0,
                "error": err_msg,
                "note": "",
            }

    return stats


def _repo() -> RunRepository:
    return RunRepository()


def list_runs() -> list[PipelineRun]:
    return _repo().list_runs()


def get_run(run_id: str) -> PipelineRun | None:
    return _repo().get_run(run_id)


def create_run(request: CreateRunRequest) -> PipelineRun:
    run = PipelineRun(
        id=str(uuid4()),
        triggeredBy=request.triggerName or "api",
        startedAt=_utc_iso(),
        currentStage="INGESTION",
        status="QUEUED",
        stages=_base_stages(),
    )
    return _repo().save_run(run)


def execute_run(run_id: str, request: CreateRunRequest) -> None:
    """Execute one run in background and persist progress to DB."""
    repo = _repo()

    run = repo.get_run(run_id)
    if not run:
        return

    run.status = "RUNNING"
    run.currentStage = "INGESTION"
    _set_stage_status(run, "INGESTION", "RUNNING")
    repo.save_run(run)

    try:
        from orchestration.langgraph.run_service import RunRequest, run_and_get_summary

        # Ingestion: scrape + normalize + load raw_tender_staging.
        ingestion_stats = _ingest_from_scrapers(per_source_limit=20)
        run = repo.get_run(run_id)
        if not run:
            return
        _set_stage_status(run, "INGESTION", "COMPLETED", details=ingestion_stats)
        for st in run.stages:
            if st.stage == "INGESTION":
                st.processedCount = int(ingestion_stats.get("normalized", 0))
                st.errorsCount = len(ingestion_stats.get("errors", {}))
                break
        _set_stage_status(
            run,
            "NORMALIZATION",
            "COMPLETED",
            details={"info": "Normalization handled during ingestion stage"},
        )
        run.currentStage = "GATEKEEPER"
        _set_stage_status(run, "GATEKEEPER", "RUNNING")
        repo.save_run(run)

        req = RunRequest(
            mode=request.mode,
            profile_id=request.profileId or "default",
            limit=request.limit,
            run_id=run_id,
        )
        summary: dict[str, Any] = run_and_get_summary(req)

        run = repo.get_run(run_id)
        if not run:
            return

        # Stage snapshots (coarse mapping for now)
        _set_stage_status(run, "INGESTION", "COMPLETED")
        _set_stage_status(run, "NORMALIZATION", "SKIPPED")
        _set_stage_status(run, "GATEKEEPER", "COMPLETED")
        _set_stage_status(run, "PRODUCTION", "COMPLETED")
        _set_stage_status(run, "OPPORTUNITY_ANALYSIS", "COMPLETED")
        _set_stage_status(run, "REVIEW", "COMPLETED")
        _set_stage_status(run, "COMPLETED", "COMPLETED")
        run.currentStage = "COMPLETED"

        gk = summary.get("gatekeeper", {})
        an = summary.get("analysis", {})
        cost = summary.get("cost", {})

        # Fill stage counters/details for UI.
        for st in run.stages:
            if st.stage == "GATEKEEPER":
                st.processedCount = int(gk.get("processed", 0))
                st.errorsCount = int(gk.get("failed", 0))
                st.details = {
                    "approved": int(gk.get("approved", 0)),
                    "needs_review": int(gk.get("needs_review", 0)),
                    "rejected": int(gk.get("rejected", 0)),
                }
            elif st.stage == "PRODUCTION":
                st.processedCount = int(gk.get("approved", 0))
            elif st.stage == "OPPORTUNITY_ANALYSIS":
                st.processedCount = int(an.get("processed", 0))
                st.errorsCount = int(an.get("failed", 0))
                st.details = {
                    "pursue": int(an.get("pursue", 0)),
                    "review": int(an.get("review", 0)),
                    "reject": int(an.get("reject", 0)),
                }
            elif st.stage == "REVIEW":
                st.processedCount = int(gk.get("needs_review", 0)) + int(an.get("review", 0))
            elif st.stage == "COMPLETED":
                st.details = {"llm_calls": int(cost.get("llm_calls", 0))}

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

        repo.save_run(run, summary=summary)
    except Exception as exc:  # noqa: BLE001
        run = repo.get_run(run_id)
        if not run:
            return

        run.status = "FAILED"
        run.currentStage = "COMPLETED"
        _set_stage_status(run, "COMPLETED", "FAILED", details={"error": str(exc)})
        for st in run.stages:
            if st.stage == "COMPLETED":
                st.errorsCount = 1
                break
        run.completedAt = _utc_iso()

        started = datetime.fromisoformat(run.startedAt)
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        completed = datetime.fromisoformat(run.completedAt)
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)
        run.durationSeconds = max(0.0, (completed - started).total_seconds())

        repo.save_run(
            run,
            error={
                "message": str(exc),
                "type": type(exc).__name__,
                "occurredAt": _utc_iso(),
            },
        )
