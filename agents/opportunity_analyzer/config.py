"""
Central config. Nothing here should be hardcoded elsewhere.
"""

from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"  # ollama default
    # 3B models drift and hallucinate more at higher temperature.
    # Keep extraction near-deterministic; analysis can have a touch more room.
    extraction_temperature: float = 0.0
    analysis_temperature: float = 0.2
    max_tokens: int = 512
    timeout_seconds: int = 30
    embedding_timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5


@dataclass
class ScoringWeights:
    keyword: float = 0.30
    location: float = 0.20
    semantic: float = 0.20
    llm_judgment: float = 0.30

    def validate(self) -> None:
        total = self.keyword + self.location + self.semantic + self.llm_judgment
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"ScoringWeights must sum to 1.0, got {total}")


@dataclass
class Thresholds:
    pursue: float = 0.70   # score >= this -> PURSUE
    reject: float = 0.35   # score <= this -> REJECT
    # between reject and pursue -> REVIEW (human needed)
    min_llm_confidence: float = 0.5  # below this, LLM signal is treated as unreliable


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    weights: ScoringWeights = field(default_factory=ScoringWeights)
    thresholds: Thresholds = field(default_factory=Thresholds)
    log_level: str = "INFO"


config = AppConfig()
config.weights.validate()
