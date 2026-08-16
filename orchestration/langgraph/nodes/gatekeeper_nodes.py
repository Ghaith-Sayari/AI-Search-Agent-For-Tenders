"""Gatekeeper-oriented LangGraph nodes.

These nodes wrap existing stable services (classifier/repositories) and keep
orchestration concerns (state updates, routing payloads) separate from business
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from time import sleep
from typing import Any
from uuid import UUID

from orchestration.langgraph.nodes.shared_nodes import record_error
from orchestration.langgraph.state import GraphState

INGESTION_PER_SOURCE_LIMIT = max(1, int(os.getenv("PIPELINE_INGESTION_PER_SOURCE_LIMIT", "20")))
GATEKEEPER_MAX_ITEMS = max(1, int(os.getenv("PIPELINE_GATEKEEPER_MAX_ITEMS", "10")))


@dataclass(slots=True)
class GatekeeperNodeDeps:
    """Runtime dependencies for gatekeeper nodes."""

    client: Any
    classifier: Any
    decision_repository: Any
    dead_letter_repository: Any | None = None
    production_publisher: Any | None = None
    source_table: str = "raw_tender_staging"
    audit_table: str = "gatekeeper_decisions"


def build_default_gatekeeper_deps(
    *,
    source_table: str = "raw_tender_staging",
    audit_table: str = "gatekeeper_decisions",
    dead_letter_table: str = "gatekeeper_dead_letter",
    production_table: str = "production_tender",
    enable_dead_letter: bool = True,
    enable_production_publish: bool = True,
) -> GatekeeperNodeDeps:
    """Build default gatekeeper dependencies from existing project services."""
    from agents.gatekeeper.audit.dead_letter_repository import GatekeeperDeadLetterRepository
    from agents.gatekeeper.audit.decision_repository import GatekeeperDecisionRepository
    from agents.gatekeeper.classifiers import GatekeeperClassifier
    from agents.gatekeeper.routing import ProductionTenderPublisher
    from db.client import get_client

    return GatekeeperNodeDeps(
        client=get_client(),
        classifier=GatekeeperClassifier(),
        decision_repository=GatekeeperDecisionRepository(table_name=audit_table),
        dead_letter_repository=(
            GatekeeperDeadLetterRepository(table_name=dead_letter_table)
            if enable_dead_letter
            else None
        ),
        production_publisher=(
            ProductionTenderPublisher(table_name=production_table)
            if enable_production_publish
            else None
        ),
        source_table=source_table,
        audit_table=audit_table,
    )


def _record_from_raw(raw_data: dict[str, Any], unique_key: str) -> Any:
    """Build RawTenderStagingRecord from raw row payload."""
    from agents.gatekeeper.schemas import RawTenderStagingRecord

    id_val = raw_data.get("id")
    return RawTenderStagingRecord(
        id=UUID(str(id_val)) if id_val else UUID(int=0),
        unique_key=unique_key,
        source=raw_data.get("source", "unknown_source"),
        title=raw_data.get("title"),
        country=raw_data.get("country"),
        posting_date=raw_data.get("posting_date"),
        deadline=raw_data.get("deadline"),
        url=raw_data.get("url"),
        description=raw_data.get("description"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        external_id=raw_data.get("external_id"),
    )


def fetch_raw_staging(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
) -> dict[str, Any]:
    """Fetch raw staging rows and store worklist in artifacts summary."""
    scope = state.get("scope", {})
    limit = scope.get("limit")
    sources = scope.get("sources", [])
    since = scope.get("since")

    query = deps.client.table(deps.source_table).select("*").order("created_at", desc=True)
    if isinstance(sources, list) and sources:
        query = query.in_("source", sources)
    if since:
        query = query.gte("created_at", since)
    if limit is not None:
        query = query.limit(limit)

    response = query.execute()
    rows = response.data or []
    # Ingestion cap: keep at most N rows per source (default: 20).
    if rows:
        per_source_count: dict[str, int] = {}
        limited_rows: list[dict[str, Any]] = []
        for row in rows:
            source = str(row.get("source") or "unknown_source")
            seen = per_source_count.get(source, 0)
            if seen >= INGESTION_PER_SOURCE_LIMIT:
                continue
            per_source_count[source] = seen + 1
            limited_rows.append(row)
        rows = limited_rows

    gatekeeper = dict(state.get("gatekeeper", {}))
    gatekeeper["fetched"] = len(rows)

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    summary["gatekeeper_raw_rows"] = rows
    summary["gatekeeper_work_items"] = rows
    artifacts["summary"] = summary

    return {
        "gatekeeper": gatekeeper,
        "artifacts": artifacts,
        "status": {"current_node": "fetch_raw_staging"},
    }


def filter_processed_gatekeeper(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
) -> dict[str, Any]:
    """Filter out already processed (unique_key, policy_version) records."""
    policy_version = state.get("run", {}).get("policy_version")
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    raw_rows = list(summary.get("gatekeeper_raw_rows", []))

    response = deps.client.table(deps.audit_table).select("unique_key,policy_version").execute()
    processed = {
        (row.get("unique_key"), row.get("policy_version"))
        for row in (response.data or [])
        if row.get("unique_key") and row.get("policy_version")
    }

    work_items: list[dict[str, Any]] = []
    skipped = 0
    for row in raw_rows:
        key = row.get("unique_key")
        if key and (key, policy_version) in processed:
            skipped += 1
            continue
        work_items.append(row)

    # Gatekeeper cap: process at most N rows (default: 10) per run.
    if len(work_items) > GATEKEEPER_MAX_ITEMS:
        skipped += len(work_items) - GATEKEEPER_MAX_ITEMS
        work_items = work_items[:GATEKEEPER_MAX_ITEMS]

    gatekeeper = dict(state.get("gatekeeper", {}))
    gatekeeper["skipped"] = gatekeeper.get("skipped", 0) + skipped

    summary["gatekeeper_work_items"] = work_items
    artifacts["summary"] = summary
    return {
        "gatekeeper": gatekeeper,
        "artifacts": artifacts,
        "status": {"current_node": "filter_processed_gatekeeper"},
    }


def prepare_gatekeeper_item(
    state: GraphState,
    *,
    index: int,
) -> dict[str, Any]:
    """Select one gatekeeper work item and build typed record."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    work_items: list[dict[str, Any]] = list(summary.get("gatekeeper_work_items", []))

    if index < 0 or index >= len(work_items):
        return {}

    raw_data = work_items[index]
    unique_key = raw_data.get("unique_key", f"raw-{index + 1}")
    record = _record_from_raw(raw_data, unique_key)

    summary["gatekeeper_current_index"] = index
    summary["gatekeeper_current_raw"] = raw_data
    summary["gatekeeper_current_record"] = record
    artifacts["summary"] = summary

    return {
        "artifacts": artifacts,
        "current": {
            "unique_key": unique_key,
            "staging_tender_id": str(raw_data.get("id")) if raw_data.get("id") else None,
            "production_tender_id": None,
            "analyzed_tender_id": None,
        },
        "status": {"current_node": "prepare_gatekeeper_item"},
    }


def classify_gatekeeper_with_retry(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
    max_retries: int = 2,
    backoff_seconds: float = 1.0,
) -> dict[str, Any]:
    """Classify current record with bounded retries for transient errors."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    record = summary.get("gatekeeper_current_record")
    if record is None:
        return {}

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            decision = deps.classifier.classify(record)
            summary["gatekeeper_current_decision"] = decision
            artifacts["summary"] = summary

            cost = dict(state.get("cost", {}))
            cost["llm_calls"] = int(cost.get("llm_calls", 0)) + 1
            if attempt > 0:
                cost["retry_attempts"] = int(cost.get("retry_attempts", 0)) + attempt

            return {
                "artifacts": artifacts,
                "cost": cost,
                "status": {"current_node": "classify_gatekeeper_with_retry"},
            }
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_retries:
                break
            sleep(backoff_seconds * (2**attempt))

    error_update = record_error(
        state,
        stage="gatekeeper.classify",
        unique_key=state.get("current", {}).get("unique_key"),
        message=str(last_exc),
        error_type=type(last_exc).__name__ if last_exc else "RuntimeError",
        retry_count=max_retries,
    )
    return {
        **error_update,
        "status": {"current_node": "classify_gatekeeper_with_retry"},
    }


def persist_gatekeeper_decision(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
) -> dict[str, Any]:
    """Persist current gatekeeper decision and update status counters."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    decision = summary.get("gatekeeper_current_decision")
    if decision is None:
        return {}

    saved = deps.decision_repository.save(decision)
    summary["gatekeeper_current_saved_decision"] = saved
    artifacts["summary"] = summary

    gatekeeper = dict(state.get("gatekeeper", {}))
    gatekeeper["processed"] = int(gatekeeper.get("processed", 0)) + 1

    status_value = getattr(decision.status, "value", str(decision.status))
    if status_value in gatekeeper:
        gatekeeper[status_value] = int(gatekeeper.get(status_value, 0)) + 1
    elif status_value == "needs_review":
        gatekeeper["needs_review"] = int(gatekeeper.get("needs_review", 0)) + 1

    return {
        "artifacts": artifacts,
        "gatekeeper": gatekeeper,
        "status": {"current_node": "persist_gatekeeper_decision"},
    }


def publish_production_tender(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
) -> dict[str, Any]:
    """Publish approved record to production_tender."""
    if deps.production_publisher is None:
        return {}

    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    record = summary.get("gatekeeper_current_record")
    decision = summary.get("gatekeeper_current_decision")
    saved_decision = summary.get("gatekeeper_current_saved_decision", {})
    if record is None or decision is None:
        return {}

    prod_row = deps.production_publisher.publish(
        record=record,
        decision=decision,
        gatekeeper_decision_id=saved_decision.get("id") if isinstance(saved_decision, dict) else None,
    )
    summary["gatekeeper_current_published"] = prod_row
    artifacts["summary"] = summary

    return {
        "artifacts": artifacts,
        "current": {
            "unique_key": state.get("current", {}).get("unique_key"),
            "staging_tender_id": state.get("current", {}).get("staging_tender_id"),
            "production_tender_id": str(prod_row.get("id")) if isinstance(prod_row, dict) else None,
            "analyzed_tender_id": None,
        },
        "status": {"current_node": "publish_production_tender"},
    }


def queue_gatekeeper_review(state: GraphState) -> dict[str, Any]:
    """Create review payload for gatekeeper needs_review outcomes."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    decision = summary.get("gatekeeper_current_decision")

    item = {
        "review_type": "gatekeeper",
        "unique_key": state.get("current", {}).get("unique_key") or "",
        "entity_id": state.get("current", {}).get("staging_tender_id"),
        "reason": getattr(decision, "decision_reason", "Manual review required"),
        "confidence_score": getattr(decision, "confidence_score", None),
        "review_id": None,
    }
    return {
        "review_queue": [item],
        "status": {"current_node": "queue_gatekeeper_review"},
    }


def write_gatekeeper_dead_letter(
    state: GraphState,
    *,
    deps: GatekeeperNodeDeps,
    stage: str = "classification_failed",
    error_type: str = "GatekeeperFailure",
    error_message: str | None = None,
    retry_count: int = 0,
) -> dict[str, Any]:
    """Persist dead-letter event for failed gatekeeper item."""
    artifacts = dict(state.get("artifacts", {}))
    summary = dict(artifacts.get("summary", {}))
    raw_payload = summary.get("gatekeeper_current_raw")
    unique_key = state.get("current", {}).get("unique_key")

    if deps.dead_letter_repository is not None:
        deps.dead_letter_repository.save(
            {
                "unique_key": unique_key,
                "policy_version": state.get("run", {}).get("policy_version"),
                "stage": stage,
                "error_type": error_type,
                "error_message": error_message or "Gatekeeper failure routed to DLQ",
                "retry_count": retry_count,
                "source_table": deps.source_table,
                "raw_payload": raw_payload,
                "last_seen_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    gatekeeper = dict(state.get("gatekeeper", {}))
    gatekeeper["dlq"] = int(gatekeeper.get("dlq", 0)) + 1

    return {
        "gatekeeper": gatekeeper,
        "status": {"current_node": "write_gatekeeper_dead_letter"},
    }
