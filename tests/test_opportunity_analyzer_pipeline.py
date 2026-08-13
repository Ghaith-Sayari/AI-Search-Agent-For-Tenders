import pytest

from pipeline.opportunity_analyzer_pipeline import OpportunityAnalyzerPipeline


class _FakeAgent:
    def __init__(self):
        self.calls = []

    def run(self, *, profile_id, limit=None, max_workers=None, continue_on_error=True):
        self.calls.append(
            {
                "profile_id": profile_id,
                "limit": limit,
                "max_workers": max_workers,
                "continue_on_error": continue_on_error,
            }
        )
        return {
            "decision_counts": {"pursue": 2, "review": 1, "reject": 3},
            "errors": 0,
            "saved": 6,
            "details": [],
        }


def test_pipeline_requires_profile_id(monkeypatch):
    monkeypatch.delenv("OPPORTUNITY_ANALYZER_PROFILE_ID", raising=False)
    pipeline = OpportunityAnalyzerPipeline(agent=_FakeAgent())
    with pytest.raises(ValueError):
        pipeline.run(limit=5)


def test_pipeline_maps_decision_counters_and_passes_args():
    fake_agent = _FakeAgent()
    pipeline = OpportunityAnalyzerPipeline(agent=fake_agent)

    summary = pipeline.run(
        profile_id="profile-123",
        limit=10,
        max_workers=4,
        continue_on_error=False,
    )

    assert fake_agent.calls[0]["profile_id"] == "profile-123"
    assert fake_agent.calls[0]["limit"] == 10
    assert fake_agent.calls[0]["max_workers"] == 4
    assert fake_agent.calls[0]["continue_on_error"] is False

    assert summary["good_fit_count"] == 2
    assert summary["needs_review_count"] == 1
    assert summary["not_fit_count"] == 3
    assert summary["failed_count"] == 0

