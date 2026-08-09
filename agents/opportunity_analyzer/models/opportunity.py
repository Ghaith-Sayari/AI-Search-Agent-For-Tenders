from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Opportunity:
    """Raw opportunity as it comes in, before any analysis."""

    # --- Required fields (No defaults) ---
    id: str
    title: str
    country: str
    description: str

    # --- Optional fields (With defaults) ---
    unique_key: Optional[str] = None
    source: Optional[str] = None
    posting_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    external_id: Optional[str] = None
    staging_tender_id: Optional[str] = None
    gatekeeper_decision_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_text: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Sanitize string fields by stripping whitespace."""
        self.id = self.id.strip() if self.id else ""
        self.title = self.title.strip() if self.title else ""
        self.country = self.country.strip() if self.country else ""
        self.description = self.description.strip() if self.description else ""

        if self.unique_key:
            self.unique_key = self.unique_key.strip()
        if self.source:
            self.source = self.source.strip()
        if self.url:
            self.url = self.url.strip()

    def full_text(self) -> str:
        """Text blob used for embedding / keyword / LLM analysis."""
        if self.raw_text:
            return self.raw_text.strip()
        
        parts = [self.title, self.description, f"Country: {self.country}"]
        return "\n".join(p for p in parts if p)

    def validate(self) -> list[str]:
        """Returns a list of validation errors, empty if valid."""
        errors: list[str] = []

        # 1. Non-empty required string validations
        if not self.id:
            errors.append("Opportunity.id is required and cannot be empty.")
        if not self.title:
            errors.append("Opportunity.title is required and cannot be empty.")
        if not self.country:
            errors.append("Opportunity.country is required and cannot be empty.")
        if not self.description:
            errors.append("Opportunity.description is required and cannot be empty.")

        # 2. Date logical validation
        if self.posting_date and self.deadline:
            if self.deadline < self.posting_date:
                errors.append(
                    f"Opportunity.deadline ({self.deadline}) cannot be earlier than "
                    f"posting_date ({self.posting_date})."
                )

        if self.created_at and self.updated_at:
            if self.updated_at < self.created_at:
                errors.append("Opportunity.updated_at cannot be earlier than created_at.")

        # 3. Simple URL Scheme Validation
        if self.url and not (self.url.startswith("http://") or self.url.startswith("https://")):
            errors.append(f"Opportunity.url ('{self.url}') must start with 'http://' or 'https://'.")

        # 4. Metadata Type Safety
        if not isinstance(self.metadata, dict):
            errors.append("Opportunity.metadata must be a dictionary.")

        return errors

    @property
    def is_valid(self) -> bool:
        """Helper to quickly check if object passes all validations."""
        return len(self.validate()) == 0