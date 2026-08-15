"""LangGraph definition for Gatekeeper + Analysis orchestration."""

from __future__ import annotations

from functools import partial
from typing import Any

from orchestration.langgraph.nodes.analysis_nodes import (
    build_default_analysis_deps,
    close_analysis_item,
    compute_deterministic_signals,
    fetch_pending_production,
    persist_analyzed_tender,
    prepare_analysis_item,
    queue_analysis_review,
    run_llm_judgment_with_retry,
    score_and_decide,
)
from orchestration.langgraph.nodes.gatekeeper_nodes import (
    build_default_gatekeeper_deps,
    classify_gatekeeper_with_retry,
    fetch_raw_staging,
    filter_processed_gatekeeper,
    persist_gatekeeper_decision,
    prepare_gatekeeper_item,
    publish_production_tender,
    queue_gatekeeper_review,
    write_gatekeeper_dead_letter,
)
from orchestration.langgraph.nodes.shared_nodes import finalize_run, start_run
from orchestration.langgraph.routing import (
    route_analysis_decision,
    route_analysis_llm_needed,
    route_gatekeeper_status,
)
from orchestration.langgraph.state import GraphState

try:
    from langgraph.graph import END, START, StateGraph
except Exception as exc:  # noqa: BLE001
    StateGraph = None
    START = "__start__"
    END = "__end__"
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _summary(state: GraphState) -> dict[str, Any]:
    return dict(state.get("artifacts", {}).get("summary", {}))


def _prepare_next_gatekeeper_item(state: GraphState) -> dict[str, Any]:
    summary = _summary(state)
    work_items = list(summary.get("gatekeeper_work_items", []))
    current_index = int(summary.get("gatekeeper_current_index", -1))
    next_index = current_index + 1

    if next_index >= len(work_items):
        artifacts = dict(state.get("artifacts", {}))
        summary["gatekeeper_has_current"] = False
        artifacts["summary"] = summary
        return {
            "artifacts": artifacts,
            "status": {"current_node": "prepare_gatekeeper_item"},
        }

    update = prepare_gatekeeper_item(state, index=next_index)
    artifacts = dict(update.get("artifacts", {}))
    summary2 = dict(artifacts.get("summary", {}))
    summary2["gatekeeper_has_current"] = True
    artifacts["summary"] = summary2
    update["artifacts"] = artifacts
    return update


def _has_gatekeeper_item(state: GraphState) -> str:
    summary = _summary(state)
    return "has_item" if bool(summary.get("gatekeeper_has_current")) else "done"


def _route_gatekeeper_decision(state: GraphState) -> str:
    summary = _summary(state)
    decision = summary.get("gatekeeper_current_decision")
    status = getattr(getattr(decision, "status", None), "value", None)
    return route_gatekeeper_status(status)


def _close_gatekeeper_item() -> dict[str, Any]:
    return {"status": {"current_node": "close_gatekeeper_item"}}


def _prepare_next_analysis_item(state: GraphState) -> dict[str, Any]:
    summary = _summary(state)
    work_items = list(summary.get("analysis_work_items", []))
    current_index = int(summary.get("analysis_current_index", -1))
    next_index = current_index + 1

    if next_index >= len(work_items):
        artifacts = dict(state.get("artifacts", {}))
        summary["analysis_has_current"] = False
        artifacts["summary"] = summary
        return {
            "artifacts": artifacts,
            "status": {"current_node": "prepare_analysis_item"},
        }

    deps = build_default_analysis_deps()
    update = prepare_analysis_item(state, deps=deps, index=next_index)
    artifacts = dict(update.get("artifacts", {}))
    summary2 = dict(artifacts.get("summary", {}))
    summary2["analysis_has_current"] = True
    artifacts["summary"] = summary2
    update["artifacts"] = artifacts
    return update


def _has_analysis_item(state: GraphState) -> str:
    summary = _summary(state)
    return "has_item" if bool(summary.get("analysis_has_current")) else "done"


def _route_analysis_llm(state: GraphState) -> str:
    summary = _summary(state)
    score = float(summary.get("analysis_deterministic_score", 0.0))
    confidence = float(summary.get("analysis_deterministic_confidence", 0.0))
    low_conf = bool(summary.get("analysis_deterministic_low_confidence", True))
    return route_analysis_llm_needed(
        deterministic_score=score,
        deterministic_confidence=confidence,
        low_confidence=low_conf,
    )


def _route_analysis_decision(state: GraphState) -> str:
    summary = _summary(state)
    final_analysis = summary.get("analysis_final")
    decision = getattr(getattr(final_analysis, "decision", None), "value", None)
    return route_analysis_decision(decision)


def build_graph(*, checkpointer: Any | None = None) -> Any:
    """Build and compile the orchestration graph."""
    if StateGraph is None:
        raise RuntimeError(
            "langgraph is not installed. Install it before building the graph."
        ) from _IMPORT_ERROR

    gk_deps = build_default_gatekeeper_deps()
    an_deps = build_default_analysis_deps()

    graph = StateGraph(GraphState)

    graph.add_node("start_run", start_run)

    # Gatekeeper lane
    graph.add_node("fetch_raw_staging", partial(fetch_raw_staging, deps=gk_deps))
    graph.add_node("filter_processed_gatekeeper", partial(filter_processed_gatekeeper, deps=gk_deps))
    graph.add_node("prepare_gatekeeper_item", _prepare_next_gatekeeper_item)
    graph.add_node(
        "classify_gatekeeper_with_retry",
        partial(classify_gatekeeper_with_retry, deps=gk_deps, max_retries=2, backoff_seconds=1.0),
    )
    graph.add_node("persist_gatekeeper_decision", partial(persist_gatekeeper_decision, deps=gk_deps))
    graph.add_node("publish_production_tender", partial(publish_production_tender, deps=gk_deps))
    graph.add_node("queue_gatekeeper_review", queue_gatekeeper_review)
    graph.add_node("close_gatekeeper_item", _close_gatekeeper_item)
    graph.add_node(
        "write_gatekeeper_dead_letter",
        partial(write_gatekeeper_dead_letter, deps=gk_deps),
    )

    # Analysis lane
    graph.add_node("fetch_pending_production", partial(fetch_pending_production, deps=an_deps))
    graph.add_node("prepare_analysis_item", _prepare_next_analysis_item)
    graph.add_node("compute_deterministic_signals", compute_deterministic_signals)
    graph.add_node(
        "run_llm_judgment_with_retry",
        partial(run_llm_judgment_with_retry, max_retries=1, backoff_seconds=1.0),
    )
    graph.add_node("score_and_decide", score_and_decide)
    graph.add_node("persist_analyzed_tender", partial(persist_analyzed_tender, deps=an_deps))
    graph.add_node("queue_analysis_review", queue_analysis_review)
    graph.add_node("close_analysis_item", close_analysis_item)

    graph.add_node("finalize_run", partial(finalize_run, terminal_status="completed"))

    # Edges
    graph.add_edge(START, "start_run")

    graph.add_edge("start_run", "fetch_raw_staging")
    graph.add_edge("fetch_raw_staging", "filter_processed_gatekeeper")
    graph.add_edge("filter_processed_gatekeeper", "prepare_gatekeeper_item")

    graph.add_conditional_edges(
        "prepare_gatekeeper_item",
        _has_gatekeeper_item,
        {"has_item": "classify_gatekeeper_with_retry", "done": "fetch_pending_production"},
    )
    graph.add_edge("classify_gatekeeper_with_retry", "persist_gatekeeper_decision")
    graph.add_conditional_edges(
        "persist_gatekeeper_decision",
        _route_gatekeeper_decision,
        {
            "publish_production_tender": "publish_production_tender",
            "queue_gatekeeper_review": "queue_gatekeeper_review",
            "close_gatekeeper_item": "close_gatekeeper_item",
            "write_gatekeeper_dead_letter": "write_gatekeeper_dead_letter",
        },
    )
    graph.add_edge("publish_production_tender", "prepare_gatekeeper_item")
    graph.add_edge("queue_gatekeeper_review", "prepare_gatekeeper_item")
    graph.add_edge("close_gatekeeper_item", "prepare_gatekeeper_item")
    graph.add_edge("write_gatekeeper_dead_letter", "prepare_gatekeeper_item")

    graph.add_edge("fetch_pending_production", "prepare_analysis_item")
    graph.add_conditional_edges(
        "prepare_analysis_item",
        _has_analysis_item,
        {"has_item": "compute_deterministic_signals", "done": "finalize_run"},
    )
    graph.add_conditional_edges(
        "compute_deterministic_signals",
        _route_analysis_llm,
        {
            "run_llm_judgment": "run_llm_judgment_with_retry",
            "skip_llm_judgment": "score_and_decide",
        },
    )
    graph.add_edge("run_llm_judgment_with_retry", "score_and_decide")
    graph.add_edge("score_and_decide", "persist_analyzed_tender")
    graph.add_conditional_edges(
        "persist_analyzed_tender",
        _route_analysis_decision,
        {
            "queue_analysis_review": "queue_analysis_review",
            "close_analysis_item": "close_analysis_item",
        },
    )
    graph.add_edge("queue_analysis_review", "prepare_analysis_item")
    graph.add_edge("close_analysis_item", "prepare_analysis_item")

    graph.add_edge("finalize_run", END)

    return graph.compile(checkpointer=checkpointer)
