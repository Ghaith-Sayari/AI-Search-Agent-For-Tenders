from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    """The org/user profile we're matching opportunities against."""

    # --- Required Fields ---
    id: str
    name: str

    # --- Optional Fields with Defaults ---
    description: str = ""
    sectors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None

    def __post_init__(self) -> None:
        """Sanitize strings and clean list elements."""
        self.id = self.id.strip() if self.id else ""
        self.name = self.name.strip() if self.name else ""
        self.description = self.description.strip() if self.description else ""

        # Remove empty items and trim spaces from list fields
        self.sectors = [s.strip() for s in self.sectors if s and s.strip()]
        self.keywords = [k.strip() for k in self.keywords if k and k.strip()]
        self.locations = [loc.strip() for loc in self.locations if loc and loc.strip()]

    def full_text(self) -> str:
        """Text blob used for embedding / keyword / LLM matching."""
        parts = [self.description]
        if self.sectors:
            parts.append("Sectors: " + ", ".join(self.sectors))
        if self.keywords:
            parts.append("Keywords: " + ", ".join(self.keywords))
        if self.locations:
            parts.append("Locations: " + ", ".join(self.locations))

        return "\n".join(p for p in parts if p)

    def validate(self) -> list[str]:
        """Returns a list of validation errors, empty if valid."""
        errors: list[str] = []

        # 1. Non-empty required strings
        if not self.id:
            errors.append("Profile.id is required and cannot be empty.")
        if not self.name:
            errors.append("Profile.name is required and cannot be empty.")

        # 2. Budget logical checks
        if self.min_budget is not None and self.min_budget < 0:
            errors.append("Profile.min_budget cannot be negative.")

        if self.max_budget is not None and self.max_budget < 0:
            errors.append("Profile.max_budget cannot be negative.")

        if (
            self.min_budget is not None
            and self.max_budget is not None
            and self.min_budget > self.max_budget
        ):
            errors.append(
                f"Profile.min_budget ({self.min_budget}) cannot be greater than "
                f"max_budget ({self.max_budget})."
            )

        return errors

    @property
    def is_valid(self) -> bool:
        """Helper to quickly check if profile passes validation."""
        return len(self.validate()) == 0