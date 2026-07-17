import pytest

from agents.gatekeeper.classifiers.settings import GatekeeperSettings


def test_from_env_requires_gatekeeper_model(monkeypatch):
    monkeypatch.setattr("agents.gatekeeper.classifiers.settings.load_dotenv", lambda: None)
    monkeypatch.delenv("GATEKEEPER_MODEL", raising=False)

    with pytest.raises(ValueError, match="GATEKEEPER_MODEL"):
        GatekeeperSettings.from_env()


def test_from_env_builds_settings_and_trims_base_url(monkeypatch):
    monkeypatch.setenv("GATEKEEPER_MODEL", "llama3.1")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    monkeypatch.setenv("GATEKEEPER_POLICY_VERSION", "2.1")
    monkeypatch.setenv("GATEKEEPER_AGENT_VERSION", "2.2")
    monkeypatch.setenv("GATEKEEPER_TEMPERATURE", "0.4")
    monkeypatch.setenv("GATEKEEPER_AUDIT_TABLE", "clean_test_db")
    monkeypatch.setenv("GATEKEEPER_LANGSMITH_TRACING", "true")
    monkeypatch.setenv("GATEKEEPER_LANGSMITH_PROJECT", "gatekeeper-observability")
    monkeypatch.setenv("GATEKEEPER_LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    monkeypatch.setenv("GATEKEEPER_LANGSMITH_API_KEY", "test-key")

    settings = GatekeeperSettings.from_env()

    assert settings.model == "llama3.1"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.policy_version == "2.1"
    assert settings.agent_version == "2.2"
    assert settings.temperature == 0.4
    assert settings.audit_table == "clean_test_db"
    assert settings.langsmith_tracing is True
    assert settings.langsmith_project == "gatekeeper-observability"
    assert settings.langsmith_endpoint == "https://api.smith.langchain.com"
    assert settings.langsmith_api_key == "test-key"
