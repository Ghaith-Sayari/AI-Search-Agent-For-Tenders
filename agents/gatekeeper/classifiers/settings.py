"""Runtime configuration for the Gatekeeper classifier."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class GatekeeperSettings:
    """Configuration loaded from environment variables, never from source code."""

    model: str
    ollama_base_url: str = "http://localhost:11434"
    policy_version: str = "1.0"
    agent_version: str = "1.0"
    temperature: float = 0.0
    audit_table: str = "gatekeeper_decisions"

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
        )
