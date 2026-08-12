from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agents.proposal_generator.models.compliance_report import ComplianceIssue
from agents.proposal_generator.models.proposal_section import ProposalSection


@dataclass
class ProposalOutput:
    """Final output payload produced by the Proposal Generator agent."""

    tender_external_id: Optional[str]
    profile_name: str
    sections: list[ProposalSection] = field(default_factory=list)
    executive_summary: str = ""
    total_score: float = 0.0  # 0..1
    confidence_score: float = 0.0  # 0..1
    decision: str = "review"  # pursue | review | reject
    compliance_issues: list[ComplianceIssue] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tender_external_id = self.tender_external_id.strip() if self.tender_external_id else None
        self.profile_name = self.profile_name.strip() if self.profile_name else ""
        self.executive_summary = self.executive_summary.strip() if self.executive_summary else ""
        self.decision = (self.decision or "review").strip().lower()

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.profile_name:
            errors.append("ProposalOutput.profile_name is required.")

        if not (0.0 <= self.total_score <= 1.0):
            errors.append("ProposalOutput.total_score must be between 0 and 1.")

        if not (0.0 <= self.confidence_score <= 1.0):
            errors.append("ProposalOutput.confidence_score must be between 0 and 1.")

        if self.decision not in {"pursue", "review", "reject"}:
            errors.append("ProposalOutput.decision must be one of: pursue, review, reject.")

        for i, section in enumerate(self.sections):
            section_errors = section.validate()
            errors.extend([f"sections[{i}]: {e}" for e in section_errors])

        for i, issue in enumerate(self.compliance_issues):
            issue_errors = issue.validate()
            errors.extend([f"compliance_issues[{i}]: {e}" for e in issue_errors])

        if not isinstance(self.metadata, dict):
            errors.append("ProposalOutput.metadata must be a dictionary.")

        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_markdown(self) -> str:
        """Render proposal as markdown text for review/export."""
        sorted_sections = sorted(self.sections, key=lambda s: s.order)
        parts: list[str] = []

        if self.executive_summary:
            parts.append("## Executive Summary\n")
            parts.append(self.executive_summary)

        for section in sorted_sections:
            parts.append(f"\n## {section.title}\n")
            parts.append(section.content)

        return "\n".join(parts).strip()
