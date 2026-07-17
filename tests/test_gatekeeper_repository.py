from uuid import uuid4

import pytest

from agents.gatekeeper.audit.decision_repository import GatekeeperDecisionRepository
from agents.gatekeeper.schemas import GatekeeperDecision, GatekeeperStatus


class _FakeExecutor:
    def __init__(self, data):
        self._data = data

    def execute(self):
        class _R:
            pass

        r = _R()
        r.data = self._data
        return r


class _FakeTable:
    def __init__(self, returned):
        self.returned = returned
        self.insert_payload = None

    def insert(self, payload):
        self.insert_payload = payload
        return _FakeExecutor(self.returned)


class _FakeClient:
    def __init__(self, returned):
        self.returned = returned
        self.requested_table = None
        self.table_obj = _FakeTable(returned)

    def table(self, table_name):
        self.requested_table = table_name
        return self.table_obj


def _decision():
    return GatekeeperDecision(
        status=GatekeeperStatus.REJECTED,
        confidence_score=0.2,
        decision_reason="spam/junk",
        cleaned_description=None,
        extracted_deadline=None,
        staging_tender_id=uuid4(),
        unique_key="raw-2",
        policy_version="1.0",
        agent_version="1.0",
    )


def test_save_inserts_decision_and_returns_first_saved_row(monkeypatch):
    fake_client = _FakeClient([{"unique_key": "raw-2", "status": "rejected"}])
    monkeypatch.setattr(
        "agents.gatekeeper.audit.decision_repository.get_client",
        lambda: fake_client,
    )

    repo = GatekeeperDecisionRepository(table_name="clean_test_db")
    row = repo.save(_decision())

    assert fake_client.requested_table == "clean_test_db"
    assert fake_client.table_obj.insert_payload["unique_key"] == "raw-2"
    assert row["status"] == "rejected"


def test_save_raises_when_supabase_returns_no_rows(monkeypatch):
    fake_client = _FakeClient([])
    monkeypatch.setattr(
        "agents.gatekeeper.audit.decision_repository.get_client",
        lambda: fake_client,
    )

    repo = GatekeeperDecisionRepository()

    with pytest.raises(RuntimeError, match="did not return"):
        repo.save(_decision())
