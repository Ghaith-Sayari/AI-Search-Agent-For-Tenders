from dataclasses import dataclass
from typing import Optional


@dataclass
class ComplianceIssue:
    """A missing or weak requirement detected during compliance review."""

    requirement_id: str
    message: str
    severity: str = "medium"  # low | medium | high
    section_key: Optional[str] = None

    def __post_init__(self) -> None:
        self.requirement_id = self.requirement_id.strip() if self.requirement_id else ""
        self.message = self.message.strip() if self.message else ""
        self.severity = (self.severity or "medium").strip().lower()
        self.section_key = self.section_key.strip() if self.section_key else None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.requirement_id:
            errors.append("ComplianceIssue.requirement_id is required.")
        if not self.message:
            errors.append("ComplianceIssue.message is required.")
        if self.severity not in {"low", "medium", "high"}:
            errors.append("ComplianceIssue.severity must be one of: low, medium, high.")
        return errors
