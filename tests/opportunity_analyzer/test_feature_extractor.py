from __future__ import annotations

from agents.opportunity_analyzer.scorers.llm_semantic_scorer import LLMSemanticScorer


def test_attach_budget_metadata_coerces_invalid_budget_source() -> None:
    payload = {"budget_source": "invalid"}
    context = {
        "method": "estimated_from_scope",
        "estimated_budget_min_eur": 100000.0,
        "estimated_budget_max_eur": 300000.0,
        "estimated_budget_mid_eur": 200000.0,
        "estimation_rationale": "unit-test",
    }
    updated = LLMSemanticScorer._attach_budget_metadata(payload, context)
    assert updated["budget_source"] == "estimated"
    assert updated["budget_eur"] == 200000.0
    assert updated["budget_range_min_eur"] == 100000.0
    assert updated["budget_range_max_eur"] == 300000.0
