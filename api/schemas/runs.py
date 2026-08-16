"""Schemas for pipeline run endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RunStatus = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "PARTIALLY_COMPLETED"]
RunStageName = Literal[
    "INGESTION",
    "NORMALIZATION",
    "GATEKEEPER",
    "PRODUCTION",
    "OPPORTUNITY_ANALYSIS",
    "REVIEW",
    "COMPLETED",
]
StageStatus = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED"]


class CreateRunRequest(BaseModel):
    triggerName: str | None = Field(default=None, description="Actor or trigger label")
    mode: Literal["full", "analysis_only", "gatekeeper_only"] = "full"
    profileId: str | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)


class PipelineStage(BaseModel):
    stage: RunStageName
    label: str
    status: StageStatus
    durationSeconds: float | None = None
    processedCount: int = 0
    errorsCount: int = 0
    retryCount: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class PipelineRun(BaseModel):
    id: str
    triggeredBy: str
    startedAt: str
    completedAt: str | None = None
    durationSeconds: float | None = None
    processedCount: int = 0
    approvedCount: int = 0
    reviewCount: int = 0
    failedCount: int = 0
    llmCallsCount: int = 0
    currentStage: RunStageName = "INGESTION"
    status: RunStatus = "QUEUED"
    stages: list[PipelineStage] = Field(default_factory=list)
