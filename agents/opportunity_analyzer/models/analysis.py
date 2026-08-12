from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Decision(str, Enum):
    PURSUE = "pursue"
    REJECT = "reject"
    REVIEW = "review"  # low confidence / needs a human


@dataclass
class SignalScore:
    """One analyzer's contribution to the overall score."""

    name: str
    score: float  # normalized 0.0 - 1.0
    weight: float  # >= 0.0
    confidence: float = 1.0  # normalized 0.0 - 1.0
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Sanitize string name."""
        self.name = self.name.strip() if self.name else ""

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    def validate(self) -> list[str]:
        """Returns a list of validation errors, empty if valid."""
        errors: list[str] = []

        if not self.name:
            errors.append("SignalScore.name is required and cannot be empty.")

        if not (0.0 <= self.score <= 1.0):
            errors.append(f"SignalScore.score must be between 0.0 and 1.0 (got {self.score}).")

        if self.weight < 0.0:
            errors.append(f"SignalScore.weight cannot be negative (got {self.weight}).")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append(
                f"SignalScore.confidence must be between 0.0 and 1.0 (got {self.confidence})."
            )

        if not isinstance(self.details, dict):
            errors.append("SignalScore.details must be a dictionary.")

        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0


@dataclass
class Analysis:
    """Full result of analyzing one opportunity against one profile."""

    # --- Required Fields ---
    opportunity_id: str
    profile_id: str

    # --- Optional Fields with Defaults ---
    signals: list[SignalScore] = field(default_factory=list)
    total_score: float = 0.0  # normalized 0.0 - 1.0
    decision: Decision = Decision.REVIEW
    reasoning: str = ""
    low_confidence: bool = False

    def __post_init__(self) -> None:
        """Sanitize string fields and ensure Enum typing."""
        self.opportunity_id = self.opportunity_id.strip() if self.opportunity_id else ""
        self.profile_id = self.profile_id.strip() if self.profile_id else ""
        self.reasoning = self.reasoning.strip() if self.reasoning else ""

        if isinstance(self.decision, str) and not isinstance(self.decision, Decision):
            self.decision = Decision(self.decision)

    def add_signal(self, signal: SignalScore) -> None:
        """Appends a signal to the analysis."""
        self.signals.append(signal)

    def signal(self, name: str) -> Optional[SignalScore]:
        """Finds a signal by name."""
        return next((s for s in self.signals if s.name == name), None)

    def get_signal_score(self, name: str, default: float = 0.0) -> float:
        """Convenience method to retrieve raw score for a named signal."""
        sig = self.signal(name)
        return sig.score if sig else default

    def recalculate_total_score(self, confidence_threshold: float = 0.7) -> float:
        """
        Recalculates total_score via the canonical scoring path in scoring.scorer
        and updates low_confidence accordingly.

        `confidence_threshold` is retained for backward compatibility and is no
        longer used here; scorer-level confidence policy is centralized in
        scoring.scorer.
        """
        del confidence_threshold
        from agents.opportunity_analyzer.scoring.scorer import compute_total_score

        total, low_confidence = compute_total_score(self.signals)
        self.total_score = total
        self.low_confidence = low_confidence
        return self.total_score

    def validate(self) -> list[str]:
        """Returns a list of validation errors, empty if valid."""
        errors: list[str] = []

        # 1. Identifier checks
        if not self.opportunity_id:
            errors.append("Analysis.opportunity_id is required and cannot be empty.")
        if not self.profile_id:
            errors.append("Analysis.profile_id is required and cannot be empty.")

        # 2. Score range check
        if not (0.0 <= self.total_score <= 1.0):
            errors.append(f"Analysis.total_score must be between 0.0 and 1.0 (got {self.total_score}).")

        # 3. Validate child signals
        for idx, sig in enumerate(self.signals):
            sig_errors = sig.validate()
            for err in sig_errors:
                errors.append(f"Analysis.signals[{idx}]: {err}")

        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0
