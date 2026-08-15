"""Pure routing rules for LangGraph conditional edges.

Keep this module deterministic and side-effect free.
"""

from __future__ import annotations

from typing import Literal


GatekeeperRoute = Literal[
    "publish_production_tender",
    "queue_gatekeeper_review",
    "close_gatekeeper_item",
    "write_gatekeeper_dead_letter",
]

AnalysisLLMRoute = Literal["run_llm_judgment", "skip_llm_judgment"]
AnalysisDecisionRoute = Literal["queue_analysis_review", "close_analysis_item"]


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def route_gatekeeper_status(status: str | None) -> GatekeeperRoute:
    """Route by gatekeeper status.

    Mapping:
    - approved     -> publish_production_tender
    - needs_review -> queue_gatekeeper_review
    - rejected     -> close_gatekeeper_item
    - expired      -> close_gatekeeper_item
    - failed/other -> write_gatekeeper_dead_letter
    """
    status_n = _norm(status)
    if status_n == "approved":
        return "publish_production_tender"
    if status_n == "needs_review":
        return "queue_gatekeeper_review"
    if status_n in {"rejected", "expired"}:
        return "close_gatekeeper_item"
    return "write_gatekeeper_dead_letter"


def route_analysis_llm_needed(
    *,
    deterministic_score: float,
    deterministic_confidence: float,
    low_confidence: bool,
    pursue_threshold: float = 0.70,
    reject_threshold: float = 0.35,
    confidence_threshold: float = 0.70,
    ambiguity_margin: float = 0.08,
) -> AnalysisLLMRoute:
    """Decide whether analysis should call LLM.

    Rule of thumb:
    - If low confidence => run LLM
    - If deterministic confidence below threshold => run LLM
    - If score in ambiguous band around pursue/reject boundaries => run LLM
    - Else skip LLM
    """
    if low_confidence:
        return "run_llm_judgment"

    if deterministic_confidence < confidence_threshold:
        return "run_llm_judgment"

    near_pursue = abs(deterministic_score - pursue_threshold) <= ambiguity_margin
    near_reject = abs(deterministic_score - reject_threshold) <= ambiguity_margin
    in_middle_band = reject_threshold < deterministic_score < pursue_threshold
    if near_pursue or near_reject or in_middle_band:
        return "run_llm_judgment"

    return "skip_llm_judgment"


def route_analysis_decision(decision: str | None) -> AnalysisDecisionRoute:
    """Route by final analysis decision."""
    if _norm(decision) == "review":
        return "queue_analysis_review"
    return "close_analysis_item"
