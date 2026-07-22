from __future__ import annotations

from agents.opportunity_analyzer.scorers.llm_semantic_scorer import LLMSemanticScorer


def test_budget_extraction_handles_euro_symbol() -> None:
    payload = LLMSemanticScorer._extract_budget_to_eur("Estimated value: 120 000 €")
    assert payload is not None
    assert payload["extracted_budget_eur"] == 120000.0


def test_it_cluster_uses_word_boundaries() -> None:
    # Contains "city" which includes "it", should not trigger IT by itself.
    assert LLMSemanticScorer._matches_it_cluster("smart city greening project") is False
    # True IT multi-signal.
    assert LLMSemanticScorer._matches_it_cluster("software platform and cloud api integration") is True


def test_estimation_prefers_civil_scope_over_generic_it() -> None:
    low, high, rationale = LLMSemanticScorer._estimate_budget_range_eur(
        "Public lighting and civil works for corridor development"
    )
    assert (low, high) == (350000.0, 2500000.0)
    assert "civil" in rationale
