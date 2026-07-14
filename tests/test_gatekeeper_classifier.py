from datetime import datetime, timezone
from uuid import uuid4

from agents.gatekeeper.classifiers import GatekeeperClassifier, GatekeeperSettings
from agents.gatekeeper.schemas import GatekeeperStatus, RawTenderStagingRecord


class FakeModels:
    def generate_content(self, **_: object):
        return type(
            "Response",
            (),
            {
                "text": (
                    '{"status":"approved","confidence_score":0.91,'
                    '"decision_reason":"Active procurement notice with a clear scope.",'
                    '"cleaned_description":"Road rehabilitation works.",'
                    '"extracted_deadline":"2026-08-01"}'
                )
            },
        )()


class FakeClient:
    models = FakeModels()


def test_classifier_returns_a_valid_auditable_decision():
    settings = GatekeeperSettings(
        gemini_api_key="test-key",
        model="test-model",
    )
    classifier = GatekeeperClassifier(
        settings=settings,
        client=FakeClient(),
        generation_config={},
    )
    record = RawTenderStagingRecord(
        id=uuid4(),
        unique_key="tender-123",
        source="example",
        title="Road rehabilitation",
        description="Tender notice for road rehabilitation works.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    decision = classifier.classify(record)

    assert decision.status is GatekeeperStatus.APPROVED
    assert decision.staging_tender_id == record.id
    assert decision.unique_key == record.unique_key
