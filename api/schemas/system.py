"""Schemas for system health and cost metrics endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ServiceStatus = Literal["UP", "DEGRADED", "DOWN"]
IncidentSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
IncidentState = Literal["OPEN", "RESOLVED"]


class SystemService(BaseModel):
    name: str
    status: ServiceStatus
    latencyMs: int | None = None
    lastCheckedAt: str
    details: dict[str, Any] = Field(default_factory=dict)


class SystemIncident(BaseModel):
    id: str
    service: str
    severity: IncidentSeverity
    status: IncidentState = "OPEN"
    createdAt: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentsStatusResponse(BaseModel):
    services: list[SystemService] = Field(default_factory=list)
    incidents: list[SystemIncident] = Field(default_factory=list)


class CostByStage(BaseModel):
    stage: str
    llmCalls: int = 0
    promptTokens: int = 0
    completionTokens: int = 0
    estimatedCostUsd: float = 0.0


class CostMetrics(BaseModel):
    periodStart: str
    periodEnd: str
    llmCalls: int = 0
    promptTokens: int = 0
    completionTokens: int = 0
    estimatedCostUsd: float = 0.0
    byStage: list[CostByStage] = Field(default_factory=list)
