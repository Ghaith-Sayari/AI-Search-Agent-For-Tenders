"""Runtime configuration for the Opportunity Analyzer classifier."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number. Got: {value!r}") from exc


def _to_int(value: Any, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer. Got: {value!r}") from exc


@dataclass(frozen=True)
class ScoreRange:
    min: float
    max: float

    def __post_init__(self) -> None:
        if self.min >= self.max:
            raise ValueError("scoring.range.min must be less than scoring.range.max")


@dataclass(frozen=True)
class ScoringWeights:
    domain_relevance: float
    geography_fit: float
    budget_fit: float
    eligibility_fit: float
    strategic_fit: float

    def __post_init__(self) -> None:
        values = (
            self.domain_relevance,
            self.geography_fit,
            self.budget_fit,
            self.eligibility_fit,
            self.strategic_fit,
        )
        if any(v < 0 for v in values):
            raise ValueError("All scoring weights must be >= 0")
        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Scoring weights must sum to 1.0. Current sum: {total}")


@dataclass(frozen=True)
class ScoringThresholds:
    good_fit_min: float
    needs_review_min: float
    not_fit_max: float

    def __post_init__(self) -> None:
        if self.good_fit_min <= self.needs_review_min:
            raise ValueError("thresholds.good_fit_min must be greater than thresholds.needs_review_min")
        if self.not_fit_max >= self.needs_review_min:
            raise ValueError("thresholds.not_fit_max must be less than thresholds.needs_review_min")


@dataclass(frozen=True)
class ConfidenceSettings:
    default: float
    min_for_auto_decision: float

    def __post_init__(self) -> None:
        for name, value in (
            ("confidence.default", self.default),
            ("confidence.min_for_auto_decision", self.min_for_auto_decision),
        ):
            if not (0 <= value <= 1):
                raise ValueError(f"{name} must be between 0 and 1. Got {value}")


@dataclass(frozen=True)
class RiskSettings:
    default_level: str
    high_risk_keywords: list[str]
    blocker_keywords: list[str]


@dataclass(frozen=True)
class DeadlineRuleSettings:
    reject_if_days_left_below: int
    warning_if_days_left_below: int


@dataclass(frozen=True)
class RuleSettings:
    hard_filters_enabled: bool
    reject_if_any_blocker: bool
    require_non_empty_description: bool
    deadline: DeadlineRuleSettings


@dataclass(frozen=True)
class ScoringConfig:
    version: str
    score_range: ScoreRange
    weights: ScoringWeights
    thresholds: ScoringThresholds
    confidence: ConfidenceSettings
    risk: RiskSettings
    rules: RuleSettings


@dataclass(frozen=True)
class OpportunityAnalyzerSettings:
    """Configuration loaded from environment + scoring YAML."""

    model: str
    ollama_base_url: str = "http://localhost:11434"
    policy_version: str = "1.0"
    agent_version: str = "1.0"
    temperature: float = 0.0
    source_table: str = "production_tender"
    audit_table: str = "opportunity_analysis"
    scoring_config_path: Path = Path("configs/scoring.yaml")
    company_profile_path: Path = Path("agents/opportunity_analyzer/profiles/company_profile.yaml")
    langsmith_tracing: bool = False
    langsmith_project: str = "opportunity-analyzer-agent"
    langsmith_endpoint: str | None = None
    langsmith_api_key: str | None = None
    scoring: ScoringConfig | None = None

    @classmethod
    def from_env(cls) -> "OpportunityAnalyzerSettings":
        load_dotenv()
        project_root = Path(__file__).resolve().parents[3]

        model = os.getenv("OPPORTUNITY_ANALYZER_MODEL")
        if not model:
            raise ValueError("OPPORTUNITY_ANALYZER_MODEL is missing from the environment variables")

        scoring_config_path = project_root / os.getenv("OPPORTUNITY_ANALYZER_SCORING_CONFIG", "configs/scoring.yaml")
        company_profile_path = project_root / os.getenv(
            "OPPORTUNITY_ANALYZER_COMPANY_PROFILE",
            "agents/opportunity_analyzer/profiles/company_profile.yaml",
        )

        scoring = cls.load_scoring_config(scoring_config_path)

        return cls(
            model=model,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            policy_version=os.getenv("OPPORTUNITY_ANALYZER_POLICY_VERSION", "1.0"),
            agent_version=os.getenv("OPPORTUNITY_ANALYZER_AGENT_VERSION", "1.0"),
            temperature=float(os.getenv("OPPORTUNITY_ANALYZER_TEMPERATURE", "0")),
            source_table=os.getenv("OPPORTUNITY_ANALYZER_SOURCE_TABLE", "production_tender"),
            audit_table=os.getenv("OPPORTUNITY_ANALYZER_AUDIT_TABLE", "opportunity_analysis"),
            scoring_config_path=scoring_config_path,
            company_profile_path=company_profile_path,
            langsmith_tracing=_as_bool(
                os.getenv("OPPORTUNITY_ANALYZER_LANGSMITH_TRACING"),
                default=_as_bool(os.getenv("LANGSMITH_TRACING"), default=False),
            ),
            langsmith_project=os.getenv(
                "OPPORTUNITY_ANALYZER_LANGSMITH_PROJECT",
                os.getenv("LANGSMITH_PROJECT", "opportunity-analyzer-agent"),
            ),
            langsmith_endpoint=os.getenv("OPPORTUNITY_ANALYZER_LANGSMITH_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT")),
            langsmith_api_key=os.getenv("OPPORTUNITY_ANALYZER_LANGSMITH_API_KEY", os.getenv("LANGSMITH_API_KEY")),
            scoring=scoring,
        )

    @staticmethod
    def load_scoring_config(path: Path) -> ScoringConfig:
        if not path.exists():
            raise FileNotFoundError(f"Scoring config not found: {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError("Scoring config root must be a mapping/object")

        version = str(raw.get("version", "1.0.0"))

        scoring_root = raw.get("scoring", {}) or {}
        scoring_range_raw = scoring_root.get("range", {}) or {}
        weights_raw = scoring_root.get("weights", {}) or {}

        thresholds_raw = raw.get("thresholds", {}) or {}
        confidence_raw = raw.get("confidence", {}) or {}
        risk_raw = raw.get("risk", {}) or {}
        rules_raw = raw.get("rules", {}) or {}
        deadline_raw = rules_raw.get("deadline", {}) or {}

        score_range = ScoreRange(
            min=_to_float(scoring_range_raw.get("min", 0), field_name="scoring.range.min"),
            max=_to_float(scoring_range_raw.get("max", 100), field_name="scoring.range.max"),
        )
        weights = ScoringWeights(
            domain_relevance=_to_float(weights_raw.get("domain_relevance", 0.35), field_name="scoring.weights.domain_relevance"),
            geography_fit=_to_float(weights_raw.get("geography_fit", 0.20), field_name="scoring.weights.geography_fit"),
            budget_fit=_to_float(weights_raw.get("budget_fit", 0.20), field_name="scoring.weights.budget_fit"),
            eligibility_fit=_to_float(weights_raw.get("eligibility_fit", 0.15), field_name="scoring.weights.eligibility_fit"),
            strategic_fit=_to_float(weights_raw.get("strategic_fit", 0.10), field_name="scoring.weights.strategic_fit"),
        )
        thresholds = ScoringThresholds(
            good_fit_min=_to_float(thresholds_raw.get("good_fit_min", 75), field_name="thresholds.good_fit_min"),
            needs_review_min=_to_float(thresholds_raw.get("needs_review_min", 50), field_name="thresholds.needs_review_min"),
            not_fit_max=_to_float(thresholds_raw.get("not_fit_max", 49.99), field_name="thresholds.not_fit_max"),
        )
        confidence = ConfidenceSettings(
            default=_to_float(confidence_raw.get("default", 0.75), field_name="confidence.default"),
            min_for_auto_decision=_to_float(
                confidence_raw.get("min_for_auto_decision", 0.65),
                field_name="confidence.min_for_auto_decision",
            ),
        )
        risk = RiskSettings(
            default_level=str(risk_raw.get("default_level", "medium")),
            high_risk_keywords=[str(x) for x in (risk_raw.get("high_risk_keywords", []) or [])],
            blocker_keywords=[str(x) for x in (risk_raw.get("blocker_keywords", []) or [])],
        )
        rules = RuleSettings(
            hard_filters_enabled=bool(rules_raw.get("hard_filters_enabled", True)),
            reject_if_any_blocker=bool(rules_raw.get("reject_if_any_blocker", True)),
            require_non_empty_description=bool(rules_raw.get("require_non_empty_description", False)),
            deadline=DeadlineRuleSettings(
                reject_if_days_left_below=_to_int(
                    deadline_raw.get("reject_if_days_left_below", 0),
                    field_name="rules.deadline.reject_if_days_left_below",
                ),
                warning_if_days_left_below=_to_int(
                    deadline_raw.get("warning_if_days_left_below", 7),
                    field_name="rules.deadline.warning_if_days_left_below",
                ),
            ),
        )

        return ScoringConfig(
            version=version,
            score_range=score_range,
            weights=weights,
            thresholds=thresholds,
            confidence=confidence,
            risk=risk,
            rules=rules,
        )
