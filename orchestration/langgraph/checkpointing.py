"""Checkpointing utilities for LangGraph orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal


CheckpointBackend = Literal["none", "memory", "sqlite"]


def create_checkpointer(
    *,
    backend: CheckpointBackend = "memory",
    sqlite_path: str | None = None,
) -> Any | None:
    """Create a LangGraph checkpointer instance.

    Backends:
    - none:   no checkpointing
    - memory: in-process checkpointer (best for local/dev)
    - sqlite: persisted local sqlite file (best for local resume/replay)
    """
    if backend == "none":
        return None

    if backend == "memory":
        try:
            from langgraph.checkpoint.memory import MemorySaver
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Memory checkpointer unavailable. Install/upgrade langgraph."
            ) from exc
        return MemorySaver()

    if backend == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "SQLite checkpointer unavailable. Install langgraph-checkpoint-sqlite."
            ) from exc

        db_path = Path(sqlite_path or ".tmp/langgraph_checkpoints.sqlite3")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return SqliteSaver.from_conn_string(str(db_path))

    raise ValueError(f"Unsupported checkpoint backend: {backend}")
