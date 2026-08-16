"""Mapper from backend analyzed/prod rows to frontend opportunity DTO."""

from __future__ import annotations

from typing import Any

from api.schemas.opportunities import AIReasoning, Opportunity, ScoreBreakdown


def _map_decision(decision: str | None) -> str:
    mapping = {
        "pursue": "GOOD_FIT",
        "review": "NEEDS_REVIEW",
        "reject": "NOT_FIT",
        "failed": "FAILED",
        "approved": "GOOD_FIT",
        "rejected": "NOT_FIT",
        "needs_review": "NEEDS_REVIEW",
    }
    return mapping.get((decision or "").strip().lower(), "NEEDS_REVIEW")


def _score_breakdown_from_signals(signals: Any) -> ScoreBreakdown:
    values = {
        "sectorRelevance": 0.0,
        "servicesRelevance": 0.0,
        "geographyRelevance": 0.0,
        "eligibilityFit": 0.0,
        "strategicFit": 0.0,
    }
    if not isinstance(signals, list):
        return ScoreBreakdown(**values)

    for sig in signals:
        if not isinstance(sig, dict):
            continue
        name = str(sig.get("name") or "").lower()
        score = float(sig.get("score") or 0.0) * 100.0
        if name == "keyword":
            values["servicesRelevance"] = score
            values["sectorRelevance"] = score
        elif name == "location":
            values["geographyRelevance"] = score
        elif name == "llm_judgment":
            values["strategicFit"] = score
            values["eligibilityFit"] = score
    return ScoreBreakdown(**values)


def _reasoning_from_signals(signals: Any, fallback_reason: str) -> AIReasoning:
    matched: list[str] = []
    missing_or_risk: list[str] = []
    recommendation = fallback_reason or ""
    if isinstance(signals, list):
        for sig in signals:
            if not isinstance(sig, dict):
                continue
            name = str(sig.get("name") or "").lower()
            details = sig.get("details") if isinstance(sig.get("details"), dict) else {}
            if name == "keyword":
                kws = details.get("matched_keywords")
                if isinstance(kws, list):
                    matched.extend([str(x) for x in kws])
            if name == "llm_judgment":
                reasoning = details.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    recommendation = reasoning.strip()
                red_flags = details.get("red_flags")
                if isinstance(red_flags, list):
                    missing_or_risk.extend([str(x) for x in red_flags])
    return AIReasoning(
        matched=matched,
        missingOrRisk=missing_or_risk,
        recommendation=recommendation,
    )


def to_opportunity(analyzed: dict[str, Any], production: dict[str, Any] | None = None) -> Opportunity:
    production = production or {}
    decision = _map_decision(str(analyzed.get("decision") or analyzed.get("status") or ""))
    confidence = float(analyzed.get("confidence_score") or 0.0) * 100.0
    llm_status = str(analyzed.get("llm_status") or "").lower()
    analysis_status = "FAILED" if llm_status in {"error", "failed", "validation_failed"} else "COMPLETED"

    signals = analyzed.get("signals", [])
    score_breakdown = _score_breakdown_from_signals(signals)
    reasoning = _reasoning_from_signals(signals, str(analyzed.get("decision_reason") or ""))

    return Opportunity(
        id=str(analyzed.get("id") or analyzed.get("production_tender_id") or analyzed.get("unique_key")),
        externalId=(
            str(production.get("external_id"))
            if production.get("external_id") is not None
            else (str(analyzed.get("unique_key")) if analyzed.get("unique_key") else None)
        ),
        title=str(analyzed.get("title") or production.get("title") or "Untitled opportunity"),
        description=(
            str(production.get("description"))
            if production.get("description") is not None
            else str(analyzed.get("decision_reason") or "")
        ),
        sector=None,
        country=str(analyzed.get("country") or production.get("country") or ""),
        countryCode=None,
        source=str(analyzed.get("source") or production.get("source") or ""),
        sourceUrl=str(analyzed.get("url") or production.get("url") or ""),
        estimatedValue=None,
        publishedDate=str(production.get("created_at") or analyzed.get("created_at") or ""),
        deadline=str(analyzed.get("deadline") or production.get("deadline") or ""),
        lastAnalyzedAt=str(analyzed.get("processed_at") or ""),
        overallScore=float(analyzed.get("total_score") or 0.0),
        decision=decision,
        confidence=confidence,
        analysisStatus=analysis_status,
        scoreBreakdown=score_breakdown,
        aiReasoning=reasoning,
        requirements=[],
        eligibilityCriteria=[],
    )
