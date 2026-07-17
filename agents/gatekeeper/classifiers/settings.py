"""Runtime configuration for the Gatekeeper classifier."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class GatekeeperSettings:
    """Configuration loaded from environment variables, never from source code."""

    model: str
    ollama_base_url: str = "http://localhost:11434"
    policy_version: str = "1.0"
    agent_version: str = "1.0"
    temperature: float = 0.0
    audit_table: str = "gatekeeper_decisions"
    langsmith_tracing: bool = False
    langsmith_project: str = "gatekeeper-agent"
    langsmith_endpoint: str | None = None
    langsmith_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "GatekeeperSettings":
        load_dotenv()

        model = os.getenv("GATEKEEPER_MODEL")
        if not model:
            raise ValueError("GATEKEEPER_MODEL is missing from the environment variables")
        
        return cls(
            model=model,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            policy_version=os.getenv("GATEKEEPER_POLICY_VERSION", "1.0"),
            agent_version=os.getenv("GATEKEEPER_AGENT_VERSION", "1.0"),
            temperature=float(os.getenv("GATEKEEPER_TEMPERATURE", "0")),
            audit_table=os.getenv("GATEKEEPER_AUDIT_TABLE", "gatekeeper_decisions"),
            langsmith_tracing=_as_bool(
                os.getenv("GATEKEEPER_LANGSMITH_TRACING"),
                default=_as_bool(os.getenv("LANGSMITH_TRACING"), default=False),
            ),
            langsmith_project=os.getenv("GATEKEEPER_LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", "gatekeeper-agent")),
            langsmith_endpoint=os.getenv("GATEKEEPER_LANGSMITH_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT")),
            langsmith_api_key=os.getenv("GATEKEEPER_LANGSMITH_API_KEY", os.getenv("LANGSMITH_API_KEY")),
        )
