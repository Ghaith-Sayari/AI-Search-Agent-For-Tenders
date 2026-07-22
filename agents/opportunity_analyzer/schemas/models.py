"""Pydantic contracts for the Opportunity Analyzer agent."""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpportunityStatus(str, Enum):
    """Final Opportunity Analyzer outcomes."""

    GOOD_FIT = "good_fit"
    NEEDS_REVIEW = "needs_review"
    NOT_FIT = "not_fit"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk label produced by the analyzer."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BudgetSource(str, Enum):
    """How budget information was obtained."""

    EXTRACTED = "extracted"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class ProductionTenderRecord(BaseModel):
    """Input row read from ``public.production_tender``."""

    id: UUID
    unique_key: str
    source: str
    title: str
    country: Optional[str] = None
    posting_date: Optional[str] = None
    deadline: date
    url: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    staging_tender_id: UUID
    gatekeeper_decision_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("unique_key", "source", "title")
    @classmethod
    def required_strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value


class OpportunityAssessment(BaseModel):
    """Scoring output fields for one production tender."""

    status: OpportunityStatus
    total_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1)
    decision_reason: str = Field(min_length=1)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    blockers: List[str] = Field(default_factory=list)
    blocker_evidence: Dict[str, str] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    budget_source: BudgetSource = BudgetSource.UNKNOWN
    budget_eur: Optional[float] = Field(default=None, ge=0)
    budget_range_min_eur: Optional[float] = Field(default=None, ge=0)
    budget_range_max_eur: Optional[float] = Field(default=None, ge=0)
    budget_estimation_rationale: Optional[str] = None

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("decision_reason")
    @classmethod
    def strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value

    @field_validator("score_breakdown")
    @classmethod
    def score_breakdown_values_must_be_valid(cls, value: Dict[str, float]) -> Dict[str, float]:
        for key, score in value.items():
            if not key.strip():
                raise ValueError("score_breakdown keys cannot be blank")
            if not (0 <= score <= 100):
                raise ValueError("Each score_breakdown value must be between 0 and 100")
        return value

    @field_validator("budget_range_max_eur")
    @classmethod
    def budget_range_must_be_ordered(cls, value: Optional[float], info):
        if value is None:
            return value
        min_value = info.data.get("budget_range_min_eur")
        if min_value is not None and value < min_value:
            raise ValueError("budget_range_max_eur must be greater than or equal to budget_range_min_eur")
        return value


class OpportunityDecision(OpportunityAssessment):
    """Structured and auditable analyzer output."""

    production_tender_id: UUID
    unique_key: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)

    @field_validator("unique_key", "policy_version", "agent_version")
    @classmethod
    def metadata_strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value
