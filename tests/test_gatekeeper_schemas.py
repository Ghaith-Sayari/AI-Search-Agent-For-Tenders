from datetime import datetime, timezone
from uuid import uuid4

import pytest

from agents.gatekeeper.schemas import (
    GatekeeperAssessment,
    GatekeeperDecision,
    GatekeeperStatus,
    RawTenderStagingRecord,
)


def _raw_record(**overrides):
    base = {
        "id": uuid4(),
        "unique_key": "  tender-123  ",
        "source": "  source-x  ",
        "title": "Title",
        "country": "TN",
        "posting_date": "2026-07-01",
        "deadline": "2026-08-01",
        "url": "https://example.com/t/1",
        "description": "desc",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "external_id": "ext-1",
    }
    base.update(overrides)
    return RawTenderStagingRecord(**base)


def test_raw_tender_staging_record_strips_required_strings():
    record = _raw_record()
    assert record.unique_key == "tender-123"
    assert record.source == "source-x"


@pytest.mark.parametrize("field", ["unique_key", "source"])
def test_raw_tender_staging_record_rejects_blank_required_strings(field):
    with pytest.raises(ValueError):
        _raw_record(**{field: "   "})


def test_gatekeeper_assessment_approved_requires_deadline():
    with pytest.raises(ValueError, match="extracted_deadline"):
        GatekeeperAssessment(
            status=GatekeeperStatus.APPROVED,
            confidence_score=0.9,
            decision_reason="Looks valid",
            cleaned_description="Clear tender scope",
            extracted_deadline=None,
        )


@pytest.mark.parametrize("status", [GatekeeperStatus.APPROVED, GatekeeperStatus.NEEDS_REVIEW])
def test_gatekeeper_assessment_approved_and_needs_review_require_cleaned_description(status):
    with pytest.raises(ValueError, match="cleaned_description"):
        GatekeeperAssessment(
            status=status,
            confidence_score=0.9,
            decision_reason="Looks valid",
            cleaned_description=None,
            extracted_deadline="2026-08-01" if status is GatekeeperStatus.APPROVED else None,
        )


def test_gatekeeper_decision_contains_audit_metadata_from_reference_flow():
    decision = GatekeeperDecision(
        status=GatekeeperStatus.NEEDS_REVIEW,
        confidence_score=0.55,
        decision_reason="Need human validation",
        cleaned_description="Need human validation",
        extracted_deadline=None,
        staging_tender_id=uuid4(),
        unique_key="raw-10",
        policy_version="1.2",
        agent_version="1.3",
    )

    assert decision.processed_at is not None
    assert decision.unique_key == "raw-10"
    assert 0 <= decision.confidence_score <= 1
