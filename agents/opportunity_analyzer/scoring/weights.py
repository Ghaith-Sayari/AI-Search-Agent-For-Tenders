from agents.opportunity_analyzer.config import ScoringWeights, config


def get_weights() -> ScoringWeights:
    return config.weights


def weight_for(signal_name: str) -> float:
    weights = get_weights()
    mapping = {
        "keyword": weights.keyword,
        "location": weights.location,
        "semantic": weights.semantic,
        "llm_judgment": weights.llm_judgment,
    }
    if signal_name not in mapping:
        raise KeyError(f"No configured weight for signal '{signal_name}'")
    return mapping[signal_name]
