"""Data access for pipeline run persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.schemas.runs import PipelineRun, PipelineStage
from db.client import get_client


class RunRepository:
    def __init__(self, table_name: str = "pipeline_runs") -> None:
        self.client = get_client()
        self.table_name = table_name

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _model_to_row(run: PipelineRun) -> dict[str, Any]:
        return {
            "id": run.id,
            "triggered_by": run.triggeredBy,
            "started_at": run.startedAt,
            "completed_at": run.completedAt,
            "duration_seconds": run.durationSeconds,
            "processed_count": run.processedCount,
            "approved_count": run.approvedCount,
            "review_count": run.reviewCount,
            "failed_count": run.failedCount,
            "llm_calls_count": run.llmCallsCount,
            "current_stage": run.currentStage,
            "status": run.status,
            "stages": [stage.model_dump() for stage in run.stages],
            "updated_at": RunRepository._now_iso(),
        }

    @staticmethod
    def _row_to_model(row: dict[str, Any]) -> PipelineRun:
        stages_raw = row.get("stages") if isinstance(row.get("stages"), list) else []
        stages: list[PipelineStage] = []
        for s in stages_raw:
            if isinstance(s, dict):
                stages.append(PipelineStage(**s))

        return PipelineRun(
            id=str(row.get("id")),
            triggeredBy=str(row.get("triggered_by") or "api"),
            startedAt=str(row.get("started_at")),
            completedAt=str(row.get("completed_at")) if row.get("completed_at") else None,
            durationSeconds=float(row.get("duration_seconds")) if row.get("duration_seconds") is not None else None,
            processedCount=int(row.get("processed_count") or 0),
            approvedCount=int(row.get("approved_count") or 0),
            reviewCount=int(row.get("review_count") or 0),
            failedCount=int(row.get("failed_count") or 0),
            llmCallsCount=int(row.get("llm_calls_count") or 0),
            currentStage=str(row.get("current_stage") or "INGESTION"),  # type: ignore[arg-type]
            status=str(row.get("status") or "QUEUED"),  # type: ignore[arg-type]
            stages=stages,
        )

    def save_run(self, run: PipelineRun, *, summary: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> PipelineRun:
        payload = self._model_to_row(run)
        if summary is not None:
            payload["summary"] = summary
        if error is not None:
            payload["error"] = error
        rows = (
            self.client.table(self.table_name)
            .upsert(payload, on_conflict="id")
            .execute()
            .data
            or []
        )
        if not rows:
            raise RuntimeError("Failed to persist pipeline run")
        return self._row_to_model(rows[0])

    def get_run(self, run_id: str) -> PipelineRun | None:
        rows = (
            self.client.table(self.table_name)
            .select("*")
            .eq("id", run_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return self._row_to_model(rows[0]) if rows else None

    def list_runs(self, limit: int = 200) -> list[PipelineRun]:
        rows = (
            self.client.table(self.table_name)
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
        return [self._row_to_model(r) for r in rows if isinstance(r, dict)]
