"""Run service for LangGraph orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from orchestration.langgraph.checkpointing import CheckpointBackend, create_checkpointer
from orchestration.langgraph.graph_def import build_graph
from orchestration.langgraph.state import GraphState, build_initial_state


@dataclass(slots=True)
class RunRequest:
    mode: str = "full"
    profile_id: str | None = None
    limit: int | None = None
    sources: list[str] | None = None
    since: str | None = None
    dry_run: bool = False
    policy_version: str = "1.0"
    gatekeeper_agent_version: str = "1.0"
    analysis_agent_version: str = "1.0"
    checkpoint_backend: CheckpointBackend = "memory"
    sqlite_checkpoint_path: str | None = None
    run_id: str | None = None


def build_state_from_request(request: RunRequest) -> GraphState:
    return build_initial_state(
        run_id=request.run_id or str(uuid4()),
        mode=request.mode,
        profile_id=request.profile_id,
        limit=request.limit,
        sources=request.sources or [],
        since=request.since,
        dry_run=request.dry_run,
        policy_version=request.policy_version,
        gatekeeper_agent_version=request.gatekeeper_agent_version,
        analysis_agent_version=request.analysis_agent_version,
    )


def run_graph(request: RunRequest) -> GraphState:
    """Compile + run the orchestration graph once and return final state."""
    checkpointer = create_checkpointer(
        backend=request.checkpoint_backend,
        sqlite_path=request.sqlite_checkpoint_path,
    )
    graph = build_graph(checkpointer=checkpointer)

    initial_state = build_state_from_request(request)
    run_id = initial_state["run"]["run_id"]

    # thread_id is required for durable checkpoint backends.
    config: dict[str, Any] = {"configurable": {"thread_id": run_id}}
    final_state = graph.invoke(initial_state, config=config)
    return final_state


def run_and_get_summary(request: RunRequest) -> dict[str, Any]:
    """Run graph and return artifacts.summary payload."""
    final_state = run_graph(request)
    return dict(final_state.get("artifacts", {}).get("summary", {}))


def render_graph_ascii(*, checkpoint_backend: CheckpointBackend = "none") -> str:
    """Return graph ASCII representation (for quick terminal inspection)."""
    checkpointer = create_checkpointer(backend=checkpoint_backend)
    graph = build_graph(checkpointer=checkpointer)
    return graph.get_graph().print_ascii()


def render_graph_mermaid(*, checkpoint_backend: CheckpointBackend = "none") -> str:
    """Return Mermaid diagram string."""
    checkpointer = create_checkpointer(backend=checkpoint_backend)
    graph = build_graph(checkpointer=checkpointer)
    return graph.get_graph().draw_mermaid()


def save_graph_png(path: str, *, checkpoint_backend: CheckpointBackend = "none") -> str:
    """Render graph to PNG file and return written path."""
    checkpointer = create_checkpointer(backend=checkpoint_backend)
    graph = build_graph(checkpointer=checkpointer)
    png_bytes = graph.get_graph().draw_mermaid_png()
    with open(path, "wb") as f:
        f.write(png_bytes)
    return path
