"""
LLM-based fit judgment analyzer.

Produces a `llm_judgment` SignalScore by:
1) extracting structured fields from opportunity text
2) asking the model to judge fit between profile and extracted details
"""

from typing import Any

from models.analysis import SignalScore
from models.opportunity import Opportunity
from models.profile import Profile
from services import llm_service
from utils.validator import validate_extraction_result


def _clamp01(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, parsed))


def analyze(opportunity: Opportunity, profile: Profile, weight: float) -> SignalScore:
    extraction = llm_service.extract(opportunity.full_text())
    if not extraction.is_usable:
        return SignalScore(
            name="llm_judgment",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={
                "stage": "extraction",
                "status": extraction.status.value,
                "error": extraction.error,
            },
        )

    extraction_errors = validate_extraction_result(extraction.data)
    if extraction_errors:
        return SignalScore(
            name="llm_judgment",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={
                "stage": "extraction_validation",
                "errors": extraction_errors,
            },
        )

    fit = llm_service.analyze_fit(profile.full_text(), extraction.data)
    if not fit.is_usable:
        return SignalScore(
            name="llm_judgment",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={
                "stage": "analysis",
                "status": fit.status.value,
                "error": fit.error,
            },
        )

    fit_score = _clamp01(fit.data.get("fit_score"), 0.5)
    confidence = _clamp01(fit.data.get("confidence"), 0.0)
    reasoning = fit.data.get("reasoning")
    red_flags = fit.data.get("red_flags")

    return SignalScore(
        name="llm_judgment",
        score=fit_score,
        weight=weight,
        confidence=confidence,
        details={
            "reasoning": reasoning if isinstance(reasoning, str) else "",
            "red_flags": red_flags if isinstance(red_flags, list) else [],
            "extracted": extraction.data,
        },
    )

