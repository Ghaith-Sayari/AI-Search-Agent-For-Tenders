from datetime import datetime, timezone
import os
from uuid import uuid4

import pytest

from agents.gatekeeper.classifiers.gatekeeper_classifier import GatekeeperClassifier
from agents.gatekeeper.classifiers.settings import GatekeeperSettings
from agents.gatekeeper.schemas import GatekeeperStatus, RawTenderStagingRecord

RAW_OUTPUT_APPROVED_MISSING_DEADLINE_KEY = (
    '{"status":"approved","confidence_score":0.95,"decision_reason":"valid tender","cleaned_description":"Cloud migration tender"}'
)
RAW_OUTPUT_APPROVED_NULL_CLEAN_DESC_AND_DEADLINE = (
    '{"status":"approved","confidence_score":0.95,"decision_reason":"valid tender","cleaned_description":null,"extracted_deadline":null}'
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeHttpClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return _FakeResponse(self.payload)


def _record():
    return RawTenderStagingRecord(
        id=uuid4(),
        unique_key="raw-1",
        source="portal-a",
        title="Cloud migration tender",
        description="description",
        deadline="24 juil. 2026",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _settings():
    return GatekeeperSettings(
        model="test-model",
        ollama_base_url="http://localhost:11434",
        policy_version="1.0",
        agent_version="1.0",
        temperature=0.0,
        audit_table="gatekeeper_decisions",
    )

def _settings_with_langsmith():
    return GatekeeperSettings(
        model="test-model",
        ollama_base_url="http://localhost:11434",
        policy_version="1.0",
        agent_version="1.0",
        temperature=0.0,
        audit_table="gatekeeper_decisions",
        langsmith_tracing=True,
        langsmith_project="gatekeeper-observability",
        langsmith_endpoint="https://api.smith.langchain.com",
        langsmith_api_key="test-key",
    )


def test_classify_posts_expected_payload_and_returns_decision(monkeypatch):
    fake_client = _FakeHttpClient(
        {
            "message": {
                "content": '{"status":"needs_review","confidence_score":0.71,"decision_reason":"insufficient details"}'
            }
        }
    )

    monkeypatch.setattr(
        GatekeeperClassifier,
        "_load_system_instructions",
        staticmethod(lambda: "SYSTEM"),
    )

    classifier = GatekeeperClassifier(settings=_settings(), client=fake_client)
    decision = classifier.classify(_record())

    assert decision.status == GatekeeperStatus.NEEDS_REVIEW
    assert decision.policy_version == "1.0"
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"] == "http://localhost:11434/api/chat"
    assert call["timeout"] == 30
    assert call["json"]["messages"][0]["content"] == "SYSTEM"
    assert call["json"]["format"] == classifier._ollama_format_schema()


def test_classify_raises_when_model_returns_empty_content(monkeypatch):
    fake_client = _FakeHttpClient({"message": {"content": ""}})
    monkeypatch.setattr(
        GatekeeperClassifier,
        "_load_system_instructions",
        staticmethod(lambda: "SYSTEM"),
    )

    classifier = GatekeeperClassifier(settings=_settings(), client=fake_client)

    with pytest.raises(RuntimeError, match="empty response"):
        classifier.classify(_record())


def test_build_record_message_excludes_internal_timestamps():
    message = GatekeeperClassifier._build_record_message(_record())

    assert "created_at" not in message
    assert "updated_at" not in message
    assert "raw-1" in message


@pytest.mark.parametrize(
    "raw_content",
    [
        RAW_OUTPUT_APPROVED_MISSING_DEADLINE_KEY,
        RAW_OUTPUT_APPROVED_NULL_CLEAN_DESC_AND_DEADLINE,
    ],
)
def test_classify_repairs_approved_outputs_with_missing_deadline(monkeypatch, raw_content):
    fake_client = _FakeHttpClient(
        {
            "message": {
                "content": raw_content
            }
        }
    )

    monkeypatch.setattr(
        GatekeeperClassifier,
        "_load_system_instructions",
        staticmethod(lambda: "SYSTEM"),
    )

    classifier = GatekeeperClassifier(settings=_settings(), client=fake_client)
    decision = classifier.classify(_record())

    assert decision.status == GatekeeperStatus.APPROVED
    assert decision.extracted_deadline is not None
    assert decision.extracted_deadline.isoformat() == "2026-07-24"


def test_classify_demotes_to_needs_review_when_approved_missing_deadline_and_no_metadata(monkeypatch):
    fake_client = _FakeHttpClient(
        {
            "message": {
                "content": RAW_OUTPUT_APPROVED_MISSING_DEADLINE_KEY
            }
        }
    )
    monkeypatch.setattr(
        GatekeeperClassifier,
        "_load_system_instructions",
        staticmethod(lambda: "SYSTEM"),
    )
    record = _record().model_copy(update={"deadline": None, "description": "desc"})
    classifier = GatekeeperClassifier(settings=_settings(), client=fake_client)
    decision = classifier.classify(record)

    assert decision.status == GatekeeperStatus.NEEDS_REVIEW
    assert decision.extracted_deadline is None
    assert decision.cleaned_description == "Cloud migration tender"


def test_classifier_configures_langsmith_env_when_enabled(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)
    monkeypatch.delenv("LANGSMITH_ENDPOINT", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.setattr(
        GatekeeperClassifier,
        "_load_system_instructions",
        staticmethod(lambda: "SYSTEM"),
    )

    GatekeeperClassifier(settings=_settings_with_langsmith(), client=_FakeHttpClient({"message": {"content": "{}"}}))

    assert os.getenv("LANGSMITH_TRACING") == "true"
    assert os.getenv("LANGSMITH_PROJECT") == "gatekeeper-observability"
    assert os.getenv("LANGSMITH_ENDPOINT") == "https://api.smith.langchain.com"
    assert os.getenv("LANGSMITH_API_KEY") == "test-key"

