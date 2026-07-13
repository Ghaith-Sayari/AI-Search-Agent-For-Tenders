from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from agents.gatekeeper.routing import ProductionTenderPublisher
from agents.gatekeeper.schemas import (
    GatekeeperDecision,
    GatekeeperStatus,
    RawTenderStagingRecord,
)


def _record() -> RawTenderStagingRecord:
    return RawTenderStagingRecord(
        id=uuid4(),
        unique_key="tender-123",
        source="example",
        title="Road rehabilitation",
        description="Raw website text.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _decision(record: RawTenderStagingRecord, status: GatekeeperStatus) -> GatekeeperDecision:
    return GatekeeperDecision(
        staging_tender_id=record.id,
        unique_key=record.unique_key,
        status=status,
        confidence_score=0.95,
        decision_reason="Test decision.",
        cleaned_description="Cleaned procurement description.",
        extracted_deadline=date(2026, 8, 1) if status is GatekeeperStatus.APPROVED else None,
        policy_version="1.0",
        agent_version="1.0",
    )


def test_publisher_rejects_non_approved_decisions():
    record = _record()

    with pytest.raises(ValueError, match="approved"):
        ProductionTenderPublisher().publish(record, _decision(record, GatekeeperStatus.REJECTED))
