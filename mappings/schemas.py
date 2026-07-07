# Location: mappings/schemas.py
"""
Canonical Data Contract for the AI Tender Assessment platform.

Every raw record scraped from any source (TendersOnTime, Beta MR, etc.)
must be mapped into this schema before it is allowed to touch the
production database or enter the LLM qualification pipeline.

See DATA_GOVERNANCE.md, Section 1.3 for the full specification.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CanonicalOpportunity(BaseModel):
    """
    The single source of truth for what a valid 'opportunity' record
    looks like, regardless of which scraper produced it.

    Mandatory fields (unique_key, source, title) are validated to
    reject empty/blank values. Any ValidationError raised here should
    be caught by the pipeline and routed to the Dead Letter Queue
    (see pipeline/dlq.py) rather than allowed to crash the batch.
    """

    unique_key: str = Field(
        ...,
        description="Deterministic MD5 hash of title + source to block duplicates",
    )
    source: str = Field(
        ...,
        description="Name of the crawler/platform source (e.g. 'tendersontime', 'beta_mr')",
    )
    title: str = Field(
        ...,
        description="Cleaned, validated title of the opportunity",
    )
    country: Optional[str] = None
    posting_date: Optional[str] = None
    deadline: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None

    @field_validator("unique_key", "source", "title")
    @classmethod
    def mandatory_fields_cannot_be_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Field cannot be empty or blank whitespace")
        return str(v).strip()

    class Config:
        # Allows the model to be instantiated from ORM-like objects
        # or dicts with extra keys silently ignored during mapping.
        extra = "ignore"
        str_strip_whitespace = True