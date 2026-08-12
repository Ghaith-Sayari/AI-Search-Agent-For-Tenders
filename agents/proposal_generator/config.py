from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProposalLLMConfig:
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    max_tokens: int = 700
    timeout_seconds: int = 45
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5


@dataclass
class ProposalGeneratorConfig:
    llm: ProposalLLMConfig

    @classmethod
    def from_env(cls) -> "ProposalGeneratorConfig":
        return cls(
            llm=ProposalLLMConfig(
                model=os.getenv("PROPOSAL_GENERATOR_MODEL", "llama3.2:3b"),
                base_url=os.getenv("PROPOSAL_GENERATOR_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
                temperature=float(os.getenv("PROPOSAL_GENERATOR_TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("PROPOSAL_GENERATOR_MAX_TOKENS", "700")),
                timeout_seconds=int(os.getenv("PROPOSAL_GENERATOR_TIMEOUT_SECONDS", "45")),
                max_retries=max(1, int(os.getenv("PROPOSAL_GENERATOR_MAX_RETRIES", "3"))),
                retry_backoff_seconds=float(os.getenv("PROPOSAL_GENERATOR_RETRY_BACKOFF", "1.5")),
            )
        )


config = ProposalGeneratorConfig.from_env()
