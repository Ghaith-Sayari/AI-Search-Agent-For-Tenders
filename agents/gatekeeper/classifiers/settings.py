"""Runtime configuration for the Gatekeeper classifier."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class GatekeeperSettings:
    """Configuration loaded from environment variables, never from source code."""

    gemini_api_key: str
    model: str
    policy_version: str = "1.0"
    agent_version: str = "1.0"
    temperature: float = 0.0
    audit_table: str = "gatekeeper_decisions"

    @classmethod
    def from_env(cls) -> "GatekeeperSettings":
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GATEKEEPER_MODEL")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from the environment variables")
        if not model:
            raise ValueError("GATEKEEPER_MODEL is missing from the environment variables")
        
        return cls(
            gemini_api_key=api_key,
            model=model,
            policy_version=os.getenv("GATEKEEPER_POLICY_VERSION", "1.0"),
            agent_version=os.getenv("GATEKEEPER_AGENT_VERSION", "1.0"),
            temperature=float(os.getenv("GATEKEEPER_TEMPERATURE", "0")),
            audit_table=os.getenv("GATEKEEPER_AUDIT_TABLE", "gatekeeper_decisions"),
        )
