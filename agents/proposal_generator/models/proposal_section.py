from dataclasses import dataclass, field


@dataclass
class ProposalSection:
    """One section of the generated proposal document."""

    key: str
    title: str
    content: str
    order: int = 0
    requirement_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.key = self.key.strip() if self.key else ""
        self.title = self.title.strip() if self.title else ""
        self.content = self.content.strip() if self.content else ""
        self.requirement_ids = [
            rid.strip() for rid in self.requirement_ids if isinstance(rid, str) and rid.strip()
        ]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.key:
            errors.append("ProposalSection.key is required.")
        if not self.title:
            errors.append("ProposalSection.title is required.")
        if not self.content:
            errors.append(f"ProposalSection.content is required for section '{self.key}'.")
        if self.order < 0:
            errors.append(f"ProposalSection.order cannot be negative for section '{self.key}'.")
        return errors
