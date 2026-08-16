"""Schemas for opportunities endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DecisionStatus = Literal["GOOD_FIT", "NEEDS_REVIEW", "NOT_FIT", "FAILED"]
AnalysisStatus = Literal["COMPLETED", "PENDING", "FAILED"]


class ScoreBreakdown(BaseModel):
    sectorRelevance: float = 0.0
    servicesRelevance: float = 0.0
    geographyRelevance: float = 0.0
    eligibilityFit: float = 0.0
    strategicFit: float = 0.0


class AIReasoning(BaseModel):
    matched: list[str] = Field(default_factory=list)
    missingOrRisk: list[str] = Field(default_factory=list)
    recommendation: str = ""


class Opportunity(BaseModel):
    id: str
    externalId: str | None = None
    title: str
    description: str | None = None
    sector: str | None = None
    country: str | None = None
    countryCode: str | None = None
    source: str | None = None
    sourceUrl: str | None = None
    estimatedValue: str | None = None
    publishedDate: str | None = None
    deadline: str | None = None
    lastAnalyzedAt: str | None = None
    overallScore: float = 0.0
    decision: DecisionStatus = "NEEDS_REVIEW"
    confidence: float = 0.0
    analysisStatus: AnalysisStatus = "COMPLETED"
    scoreBreakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    aiReasoning: AIReasoning = Field(default_factory=AIReasoning)
    requirements: list[str] = Field(default_factory=list)
    eligibilityCriteria: list[str] = Field(default_factory=list)
