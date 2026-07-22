from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from agents.opportunity_analyzer.classifiers.settings import OpportunityAnalyzerSettings
from agents.opportunity_analyzer.schemas.models import (
    BudgetSource,
    OpportunityDecision,
    OpportunityStatus,
    ProductionTenderRecord,
    RiskLevel,
)
from pipeline.opportunity_analyzer_pipeline import OpportunityAnalyzerPipeline


ROOT = Path(__file__).resolve().parents[2]


def _settings() -> OpportunityAnalyzerSettings:
    scoring_path = ROOT / "configs" / "scoring.yaml"
    profile_path = ROOT / "agents" / "opportunity_analyzer" / "profiles" / "company_profile.yaml"
    return OpportunityAnalyzerSettings(
        model="test-model",
        scoring=OpportunityAnalyzerSettings.load_scoring_config(scoring_path),
        scoring_config_path=scoring_path,
        company_profile_path=profile_path,
    )


@dataclass
class _StubClassifier:
    settings: OpportunityAnalyzerSettings

    def classify(self, record: ProductionTenderRecord) -> OpportunityDecision:
        return OpportunityDecision(
            production_tender_id=record.id,
            unique_key=record.unique_key,
            status=OpportunityStatus.GOOD_FIT,
            total_score=80.0,
            confidence_score=0.9,
            decision_reason="stub",
            risk_level=RiskLevel.LOW,
            score_breakdown={
                "domain_relevance": 80.0,
                "geography_fit": 80.0,
                "budget_fit": 80.0,
                "eligibility_fit": 80.0,
                "strategic_fit": 80.0,
            },
            blockers=[],
            blocker_evidence={},
            strengths=[],
            gaps=[],
            budget_source=BudgetSource.ESTIMATED,
            budget_eur=200000.0,
            budget_range_min_eur=100000.0,
            budget_range_max_eur=300000.0,
            budget_estimation_rationale="stub",
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
        )


class _StubRepo:
    def __init__(self, processed: set[str]) -> None:
        self.processed = processed
        self.saved = []

    def get_processed_keys(self, _policy_version: str) -> set[str]:
        return set(self.processed)

    def save(self, decision: OpportunityDecision):
        self.saved.append(decision)
        return {"id": str(uuid4())}


def _raw(unique_key: str) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid4()),
        "unique_key": unique_key,
        "source": "unit-test",
        "title": f"Tender {unique_key}",
        "country": "Morocco",
        "posting_date": now.date().isoformat(),
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        "url": "https://example.com",
        "description": "desc",
        "external_id": None,
        "staging_tender_id": str(uuid4()),
        "gatekeeper_decision_id": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def test_pipeline_skips_already_processed_records(monkeypatch) -> None:
    classifier = _StubClassifier(settings=_settings())
    pipeline = OpportunityAnalyzerPipeline(classifier=classifier)
    stub_repo = _StubRepo(processed={"a"})
    pipeline.audit_repository = stub_repo

    monkeypatch.setattr(
        pipeline,
        "fetch_source_records",
        lambda limit=None, offset=0: [_raw("a"), _raw("b"), _raw("c")],
    )

    summary = pipeline.run(limit=3)
    assert summary["skipped"] == 1
    assert summary["processed"] == 2
    assert summary["good_fit_count"] == 2
    assert len(stub_repo.saved) == 2
