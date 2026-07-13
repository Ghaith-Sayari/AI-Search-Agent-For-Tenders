"""Pydantic contracts between raw tender staging and the Gatekeeper."""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GatekeeperStatus(str, Enum):
    """Allowed outcomes for a staged tender."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    EXPIRED = "expired"
    FAILED = "failed"


class RawTenderStagingRecord(BaseModel):
    """A row read from ``public.raw_tender_staging`` before Gatekeeper review."""

    id: UUID
    unique_key: str
    source: str
    title: Optional[str] = None
    country: Optional[str] = None
    posting_date: Optional[str] = None
    deadline: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    external_id: Optional[str] = None

    # The staging table may return columns such as embedding that the
    # Gatekeeper does not need to inspect.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("unique_key", "source")
    @classmethod
    def required_strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value


class GatekeeperAssessment(BaseModel):
    """The decision fields the LLM is permitted to produce."""

    status: GatekeeperStatus
    confidence_score: float = Field(ge=0, le=1)
    decision_reason: str = Field(min_length=1)
    cleaned_description: Optional[str] = None
    extracted_deadline: Optional[date] = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("decision_reason")
    @classmethod
    def strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value

    @model_validator(mode="after")
    def approved_tenders_require_a_deadline(self) -> "GatekeeperAssessment":
        if self.status is GatekeeperStatus.APPROVED and self.extracted_deadline is None:
            raise ValueError("Approved tenders require an extracted_deadline")
        return self


class GatekeeperDecision(GatekeeperAssessment):
    """Structured, auditable outcome returned for one staging record."""

    staging_tender_id: UUID
    unique_key: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    policy_version: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)

    @field_validator("unique_key", "policy_version", "agent_version")
    @classmethod
    def metadata_strings_cannot_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty or blank")
        return value
