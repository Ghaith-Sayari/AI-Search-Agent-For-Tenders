import pytest

from agents.gatekeeper.audit.dead_letter_repository import GatekeeperDeadLetterRepository


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
        self.upsert_payload = None
        self.on_conflict = None

    def upsert(self, payload, on_conflict=None):
        self.upsert_payload = payload
        self.on_conflict = on_conflict
        return _FakeExecutor(self.returned)


class _FakeClient:
    def __init__(self, returned):
        self.returned = returned
        self.requested_table = None
        self.table_obj = _FakeTable(returned)

    def table(self, table_name):
        self.requested_table = table_name
        return self.table_obj


def test_save_upserts_dead_letter_item(monkeypatch):
    fake_client = _FakeClient([{"unique_key": "raw-1"}])
    monkeypatch.setattr(
        "agents.gatekeeper.audit.dead_letter_repository.get_client",
        lambda: fake_client,
    )

    repo = GatekeeperDeadLetterRepository()
    row = repo.save(
        {
            "unique_key": "raw-1",
            "policy_version": "1.0",
            "stage": "classification_exception",
            "error_type": "RuntimeError",
            "error_message": "boom",
            "retry_count": 3,
        }
    )

    assert fake_client.requested_table == "gatekeeper_dead_letter"
    assert fake_client.table_obj.on_conflict == "unique_key,policy_version"
    assert row["unique_key"] == "raw-1"


def test_save_raises_when_supabase_returns_no_rows(monkeypatch):
    fake_client = _FakeClient([])
    monkeypatch.setattr(
        "agents.gatekeeper.audit.dead_letter_repository.get_client",
        lambda: fake_client,
    )

    repo = GatekeeperDeadLetterRepository()
    with pytest.raises(RuntimeError, match="did not return"):
        repo.save(
            {
                "unique_key": "raw-1",
                "policy_version": "1.0",
                "stage": "classification_exception",
                "error_type": "RuntimeError",
                "error_message": "boom",
                "retry_count": 3,
            }
        )

