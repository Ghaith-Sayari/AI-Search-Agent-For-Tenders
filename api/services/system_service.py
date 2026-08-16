"""Service layer for system status and cost metrics."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import requests

from api.schemas.system import (
    AgentsStatusResponse,
    CostByStage,
    CostMetrics,
    SystemIncident,
    SystemService,
)
from api.services.run_service import list_runs


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _service_check(name: str, fn: Any) -> SystemService:
    started = time.perf_counter()
    now = _utc_now()
    try:
        details = fn() or {}
        latency = int((time.perf_counter() - started) * 1000)
        return SystemService(
            name=name,
            status="UP",
            latencyMs=latency,
            lastCheckedAt=_iso(now),
            details=details if isinstance(details, dict) else {"info": str(details)},
        )
    except Exception as exc:  # noqa: BLE001
        latency = int((time.perf_counter() - started) * 1000)
        return SystemService(
            name=name,
            status="DOWN",
            latencyMs=latency,
            lastCheckedAt=_iso(now),
            details={"error": str(exc)},
        )


class SystemServiceLayer:
    def get_agents_status(self) -> AgentsStatusResponse:
        services: list[SystemService] = [
            _service_check("database_supabase", self._check_supabase),
            _service_check("llm_ollama", self._check_ollama),
            _service_check("orchestration_langgraph", self._check_langgraph),
            _service_check("api_runtime", self._check_runtime),
        ]

        incidents: list[SystemIncident] = []
        for s in services:
            if s.status == "DOWN":
                incidents.append(
                    SystemIncident(
                        id=str(uuid4()),
                        service=s.name,
                        severity="HIGH",
                        status="OPEN",
                        createdAt=s.lastCheckedAt,
                        message=f"{s.name} is DOWN",
                        metadata=s.details,
                    )
                )

        # Add failed recent runs as incidents
        for run in list_runs()[:25]:
            if run.status == "FAILED":
                incidents.append(
                    SystemIncident(
                        id=str(uuid4()),
                        service="pipeline_run",
                        severity="MEDIUM",
                        status="OPEN",
                        createdAt=run.completedAt or run.startedAt,
                        message=f"Pipeline run failed: {run.id}",
                        metadata={"runId": run.id, "currentStage": run.currentStage},
                    )
                )

        return AgentsStatusResponse(services=services, incidents=incidents)

    def get_cost_metrics(self, *, days: int = 7) -> CostMetrics:
        now = _utc_now()
        period_start = now - timedelta(days=max(1, days))
        runs = [
            r
            for r in list_runs()
            if datetime.fromisoformat(r.startedAt.replace("Z", "+00:00")) >= period_start
        ]

        llm_calls = sum(int(r.llmCallsCount or 0) for r in runs)
        prompt_tokens = 0
        completion_tokens = 0
        estimated_cost = 0.0

        # Placeholder stage split until token/cost telemetry is persisted per stage.
        by_stage = [
            CostByStage(stage="GATEKEEPER", llmCalls=llm_calls, promptTokens=0, completionTokens=0, estimatedCostUsd=0.0),
            CostByStage(stage="OPPORTUNITY_ANALYSIS", llmCalls=0, promptTokens=0, completionTokens=0, estimatedCostUsd=0.0),
        ]

        return CostMetrics(
            periodStart=_iso(period_start),
            periodEnd=_iso(now),
            llmCalls=llm_calls,
            promptTokens=prompt_tokens,
            completionTokens=completion_tokens,
            estimatedCostUsd=estimated_cost,
            byStage=by_stage,
        )

    @staticmethod
    def _check_runtime() -> dict[str, Any]:
        return {"python": os.sys.version.split()[0]}

    @staticmethod
    def _check_langgraph() -> dict[str, Any]:
        import importlib.util

        found = importlib.util.find_spec("langgraph") is not None
        if not found:
            raise RuntimeError("langgraph package not installed")
        return {"installed": True}

    @staticmethod
    def _check_supabase() -> dict[str, Any]:
        from db.client import get_client

        client = get_client()
        # Lightweight query
        _ = client.table("production_tender").select("id").limit(1).execute()
        return {"connected": True}

    @staticmethod
    def _check_ollama() -> dict[str, Any]:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        response.raise_for_status()
        data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        models = data.get("models", []) if isinstance(data, dict) else []
        return {"baseUrl": base_url, "modelsCount": len(models)}
