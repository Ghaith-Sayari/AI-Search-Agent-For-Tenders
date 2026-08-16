"""Analysis-oriented LangGraph nodes (persisting to analyzed_tender only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from time import sleep
from typing import Any

from orchestration.langgraph.nodes.shared_nodes import record_error
from orchestration.langgraph.state import GraphState

ANALYSIS_MAX_ITEMS = max(1, int(os.getenv("PIPELINE_ANALYSIS_MAX_ITEMS", "5")))


@dataclass(slots=True)
class AnalysisNodeDeps:
    """Runtime dependencies for analysis nodes."""

    client: Any
    source_table: str = "production_tender"
    target_table: str = "analyzed_tender"
    profile_table: str = "profiles"


def build_default_analysis_deps(
    *,
    source_table: str = "production_tender",
    target_table: str = "analyzed_tender",
    profile_table: str = "profiles",
) -> AnalysisNodeDeps:
    """Build default analysis dependencies from existing project services."""
    from db.client import get_client

    return AnalysisNodeDeps(
        client=get_client(),
        source_table=source_table,
        target_table=target_table,
        profile_table=profile_table,
    )


def _build_opportunity(raw: dict[str, Any], index: int) -> Any:
    from agents.opportunity_analyzer.models.opportunity import Opportunity

    unique_key = str(raw.get("unique_key") or f"prod-{index}")
    title = str(raw.get("title") or "").strip() or f"Untitled tender {unique_key}"
    country = str(raw.get("country") or "").strip() or "unknown"
    description = str(raw.get("description") or "").strip() or "No description provided."

    return Opportunity(
        id=str(raw.get("id") or unique_key),
        unique_key=unique_key,
        source=raw.get("source"),
        title=title,
        country=country,
        description=description,
        url=raw.get("url"),
        external_id=raw.get("external_id"),
        staging_tender_id=str(raw.get("staging_tender_id")) if raw.get("staging_tender_id") else None,
        gatekeeper_decision_id=str(raw.get("gatekeeper_decision_id")) if raw.get("gatekeeper_decision_id") else None,
        raw_text=raw.get("raw_text") if isinstance(raw.get("raw_text"), str) else None,
        metadata={"deadline": raw.get("deadline"), "posting_date": raw.get("posting_date")},
    )


def _build_profile(row: dict[str, Any], fallback_id: str) -> Any:
    from agents.opportunity_analyzer.models.profile import Profile

    return Profile(
        id=str(row.get("id") or fallback_id),
        name=str(row.get("name") or "Unnamed profile"),
        description=str(row.get("description") or ""),
        sectors=row.get("sectors") if isinstance(row.get("sectors"), list) else [],
        keywords=row.get("keywords") if isinstance(row.get("keywords"), list) else [],
        locations=row.get("locations") if isinstance(row.get("locations"), list) else [],
        min_budget=row.get("min_budget"),
        max_budget=row.get("max_budget"),
    )


def _signal_payload(signal: Any) -> dict[str, Any]:
    return {
        "name": signal.name,
        "score": signal.score,
        "weight": signal.weight,
        "confidence": signal.confidence,
        "weighted_score": round(signal.weighted_score, 6),
        "details": signal.details,
    }


def _confidence_from_signals(signals: list[Any]) -> float:
    total_weight = sum(max(0.0, s.weight) for s in signals) or 1.0
    confidence_score = sum((max(0.0, s.weight) * s.confidence) for s in signals) / total_weight
    return round(confidence_score, 6)


def fetch_pending_production(
    state: GraphState,
    *,
    deps: AnalysisNodeDeps,
) -> dict[str, Any]:
    """Fetch production records pending analysis for current profile/policy."""
    scope = state.get("scope", {})
    run = state.get("run", {})
    limit = scope.get("limit")
    since = scope.get("since")
    profile_id = run.get("profile_id")
    policy_version = run.get("policy_version")
    if not profile_id:
        raise ValueError("run.profile_id is required for analysis flow")

    query = deps.client.table(deps.source_table).select("*").order("created_at", desc=True)
    if since:
        query = query.gte("created_at", since)
    if limit is not None:
        query = query.limit(limit)

    source_rows = query.execute().data or []
    analyzed_rows = (
        deps.client.table(deps.target_table)
        .select("unique_key")
        .eq("profile_id", profile_id)
        .eq("policy_version", policy_version)
        .execute()
        .data
        or []
    )
    processed_keys = {str(r.get("unique_key")) for r in analyzed_rows if r.get("unique_key")}

    work_items: list[dict[str, Any]] = []
    skipped = 0
    for row in source_rows:
        key = str(row.get("unique_key") or "")
        if key and key in processed_keys:
            skipped += 1
            continue
        work_items.append(row)

    # Analysis cap: process at most N rows (default: 5) per run.
    if len(work_items) > ANALYSIS_MAX_ITEMS:
        skipped += len(work_items) - ANALYSIS_MAX_ITEMS
        work_items = work_items[:ANALYSIS_MAX_ITEMS]

    analysis = dict(state.get("analysis", {}))
    analysis["fetched"] = len(source_rows)
    analysis["skipped"] = int(analysis.get("skipped", 0)) + skipped

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    summary["analysis_work_items"] = work_items
    artifacts["summary"] = summary

    return {
        "analysis": analysis,
        "artifacts": artifacts,
        "status": {"current_node": "fetch_pending_production"},
    }


def prepare_analysis_item(
    state: GraphState,
    *,
    deps: AnalysisNodeDeps,
    index: int,
) -> dict[str, Any]:
    """Prepare current analysis item (opportunity + profile)."""
    run = state.get("run", {})
    profile_id = run.get("profile_id")
    if not profile_id:
        raise ValueError("run.profile_id is required for analysis flow")

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    work_items: list[dict[str, Any]] = list(summary.get("analysis_work_items", []))
    if index < 0 or index >= len(work_items):
        return {}

    raw = work_items[index]
    opportunity = _build_opportunity(raw, index + 1)

    profile_row = (
        deps.client.table(deps.profile_table).select("*").eq("id", profile_id).single().execute().data
    )
    if not profile_row:
        raise ValueError(f"Profile '{profile_id}' not found in table '{deps.profile_table}'")
    profile = _build_profile(profile_row, profile_id)

    summary["analysis_current_index"] = index
    summary["analysis_current_raw"] = raw
    summary["analysis_current_opportunity"] = opportunity
    summary["analysis_current_profile"] = profile
    artifacts["summary"] = summary

    return {
        "artifacts": artifacts,
        "current": {
            "unique_key": opportunity.unique_key,
            "staging_tender_id": None,
            "production_tender_id": str(raw.get("id")) if raw.get("id") else None,
            "analyzed_tender_id": None,
        },
        "status": {"current_node": "prepare_analysis_item"},
    }


def compute_deterministic_signals(state: GraphState) -> dict[str, Any]:
    """Run deterministic analysis signals (keyword/location only)."""
    from agents.opportunity_analyzer.analyzers import keyword_analyzer, location_analyzer
    from agents.opportunity_analyzer.models.analysis import Analysis
    from agents.opportunity_analyzer.scoring.decision import decide
    from agents.opportunity_analyzer.scoring.scorer import score_analysis
    from agents.opportunity_analyzer.scoring.weights import weight_for

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    opportunity = summary.get("analysis_current_opportunity")
    profile = summary.get("analysis_current_profile")
    if opportunity is None or profile is None:
        return {}

    analysis = Analysis(opportunity_id=opportunity.id, profile_id=profile.id)
    analysis.add_signal(keyword_analyzer.analyze(opportunity, profile, weight_for("keyword")))
    analysis.add_signal(location_analyzer.analyze(opportunity, profile, weight_for("location")))
    score_analysis(analysis)
    decide(analysis)

    summary["analysis_deterministic"] = analysis
    summary["analysis_deterministic_score"] = float(analysis.total_score)
    summary["analysis_deterministic_confidence"] = _confidence_from_signals(analysis.signals)
    summary["analysis_deterministic_low_confidence"] = bool(analysis.low_confidence)
    artifacts["summary"] = summary

    return {
        "artifacts": artifacts,
        "status": {"current_node": "compute_deterministic_signals"},
    }


def run_llm_judgment_with_retry(
    state: GraphState,
    *,
    max_retries: int = 1,
    backoff_seconds: float = 1.0,
) -> dict[str, Any]:
    """Run LLM judgment analyzer with bounded retries."""
    from agents.opportunity_analyzer.analyzers import llm_judgment_analyzer
    from agents.opportunity_analyzer.scoring.weights import weight_for

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    opportunity = summary.get("analysis_current_opportunity")
    profile = summary.get("analysis_current_profile")
    if opportunity is None or profile is None:
        return {}

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            llm_signal = llm_judgment_analyzer.analyze(
                opportunity,
                profile,
                weight_for("llm_judgment"),
            )
            summary["analysis_llm_signal"] = llm_signal
            artifacts["summary"] = summary

            cost = dict(state.get("cost", {}))
            cost["llm_calls"] = int(cost.get("llm_calls", 0)) + 1
            if attempt > 0:
                cost["retry_attempts"] = int(cost.get("retry_attempts", 0)) + attempt

            return {
                "artifacts": artifacts,
                "cost": cost,
                "status": {"current_node": "run_llm_judgment_with_retry"},
            }
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_retries:
                break
            sleep(backoff_seconds * (2**attempt))

    error_update = record_error(
        state,
        stage="analysis.llm_judgment",
        unique_key=state.get("current", {}).get("unique_key"),
        message=str(last_exc),
        error_type=type(last_exc).__name__ if last_exc else "RuntimeError",
        retry_count=max_retries,
    )
    return {
        **error_update,
        "status": {"current_node": "run_llm_judgment_with_retry"},
    }


def score_and_decide(state: GraphState) -> dict[str, Any]:
    """Combine deterministic + optional LLM signal, then compute final decision."""
    from agents.opportunity_analyzer.models.analysis import Analysis
    from agents.opportunity_analyzer.scoring.decision import decide
    from agents.opportunity_analyzer.scoring.scorer import score_analysis

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    opportunity = summary.get("analysis_current_opportunity")
    profile = summary.get("analysis_current_profile")
    deterministic = summary.get("analysis_deterministic")
    if opportunity is None or profile is None:
        return {}

    final_analysis = Analysis(opportunity_id=opportunity.id, profile_id=profile.id)
    if deterministic is not None:
        for sig in deterministic.signals:
            final_analysis.add_signal(sig)

    llm_signal = summary.get("analysis_llm_signal")
    if llm_signal is not None:
        final_analysis.add_signal(llm_signal)

    score_analysis(final_analysis)
    decide(final_analysis)

    summary["analysis_final"] = final_analysis
    artifacts["summary"] = summary

    analysis = dict(state.get("analysis", {}))
    analysis["processed"] = int(analysis.get("processed", 0)) + 1
    decision_name = str(final_analysis.decision.value)
    if decision_name in {"pursue", "review", "reject"}:
        analysis[decision_name] = int(analysis.get(decision_name, 0)) + 1
    else:
        analysis["failed"] = int(analysis.get("failed", 0)) + 1

    return {
        "analysis": analysis,
        "artifacts": artifacts,
        "status": {"current_node": "score_and_decide"},
    }


def persist_analyzed_tender(
    state: GraphState,
    *,
    deps: AnalysisNodeDeps,
) -> dict[str, Any]:
    """Persist final analysis to analyzed_tender."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    final_analysis = summary.get("analysis_final")
    raw = summary.get("analysis_current_raw", {})
    if final_analysis is None:
        return {}

    llm_signal = next((s for s in final_analysis.signals if s.name == "llm_judgment"), None)
    keyword_signal = next((s for s in final_analysis.signals if s.name == "keyword"), None)
    location_signal = next((s for s in final_analysis.signals if s.name == "location"), None)

    llm_status = "ok" if llm_signal else "skipped"
    llm_error = None
    if llm_signal and isinstance(llm_signal.details, dict):
        llm_status = str(llm_signal.details.get("status") or llm_status)
        llm_error = llm_signal.details.get("error")

    matched_keywords: list[str] = []
    if keyword_signal and isinstance(keyword_signal.details, dict):
        raw_m = keyword_signal.details.get("matched_keywords")
        if isinstance(raw_m, list):
            matched_keywords = [str(x) for x in raw_m]

    location_match_type = "unknown"
    if location_signal and isinstance(location_signal.details, dict):
        location_match_type = str(
            location_signal.details.get("match_type")
            or location_signal.details.get("reason")
            or location_match_type
        )

    payload = {
        "production_tender_id": str(raw.get("id")) if raw.get("id") else None,
        "unique_key": str(raw.get("unique_key") or final_analysis.opportunity_id),
        "profile_id": str(state.get("run", {}).get("profile_id")),
        "source": raw.get("source"),
        "title": raw.get("title"),
        "country": raw.get("country"),
        "deadline": raw.get("deadline"),
        "url": raw.get("url"),
        "decision": final_analysis.decision.value,
        "total_score": round(float(final_analysis.total_score) * 100.0, 2),
        "total_score_normalized": round(float(final_analysis.total_score), 6),
        "confidence_score": _confidence_from_signals(final_analysis.signals),
        "low_confidence": bool(final_analysis.low_confidence),
        "decision_reason": final_analysis.reasoning or "Scored by Opportunity Analyzer",
        "llm_status": llm_status,
        "llm_error": str(llm_error) if llm_error else None,
        "matched_keywords": matched_keywords,
        "location_match_type": location_match_type,
        "signals": [_signal_payload(s) for s in final_analysis.signals],
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": state.get("run", {}).get("policy_version"),
        "agent_version": state.get("run", {}).get("analysis_agent_version", "1.0"),
    }

    saved = (
        deps.client.table(deps.target_table)
        .upsert(payload, on_conflict="unique_key,profile_id,policy_version")
        .execute()
        .data
    )
    row = saved[0] if isinstance(saved, list) and saved else None
    summary["analysis_saved_row"] = row
    artifacts["summary"] = summary

    return {
        "artifacts": artifacts,
        "current": {
            "unique_key": state.get("current", {}).get("unique_key"),
            "staging_tender_id": state.get("current", {}).get("staging_tender_id"),
            "production_tender_id": state.get("current", {}).get("production_tender_id"),
            "analyzed_tender_id": str(row.get("id")) if isinstance(row, dict) and row.get("id") else None,
        },
        "status": {"current_node": "persist_analyzed_tender"},
    }


def queue_analysis_review(state: GraphState) -> dict[str, Any]:
    """Create review payload for analysis review outcomes."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    final_analysis = summary.get("analysis_final")
    item = {
        "review_type": "analysis",
        "unique_key": state.get("current", {}).get("unique_key") or "",
        "entity_id": state.get("current", {}).get("analyzed_tender_id")
        or state.get("current", {}).get("production_tender_id"),
        "reason": getattr(final_analysis, "reasoning", "") or "Manual review required",
        "confidence_score": _confidence_from_signals(final_analysis.signals)
        if final_analysis is not None
        else None,
        "review_id": None,
    }
    return {
        "review_queue": [item],
        "status": {"current_node": "queue_analysis_review"},
    }


def close_analysis_item(state: GraphState | None = None) -> dict[str, Any]:
    """No-op terminal node for analysis item closure."""
    return {"status": {"current_node": "close_analysis_item"}}
