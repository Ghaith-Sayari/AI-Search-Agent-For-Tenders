from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agents.gatekeeper.schemas import GatekeeperDecision, GatekeeperStatus, RawTenderStagingRecord


def test_staging_record_accepts_database_shape_and_ignores_embedding():
    record = RawTenderStagingRecord(
        id=uuid4(),
        unique_key="tender-123",
        source="beta_mr",
        title="Road construction",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        embedding=[0.1, 0.2],
    )

    assert record.source == "beta_mr"


def test_approved_decision_requires_structured_deadline():
    with pytest.raises(ValidationError, match="extracted_deadline"):
        GatekeeperDecision(
            staging_tender_id=uuid4(),
            unique_key="tender-123",
            status=GatekeeperStatus.APPROVED,
            confidence_score=0.95,
            decision_reason="Active public procurement notice.",
            policy_version="1.0",
            agent_version="1.0",
        )


def test_valid_rejected_decision_is_accepted():
    decision = GatekeeperDecision(
        staging_tender_id=uuid4(),
        unique_key="tender-123",
        status=GatekeeperStatus.REJECTED,
        confidence_score=0.98,
        decision_reason="Registration page, not a procurement opportunity.",
        cleaned_description="Create an account.",
        extracted_deadline=date(2026, 8, 1),
        policy_version="1.0",
        agent_version="1.0",
    )

    assert decision.status == GatekeeperStatus.REJECTED
