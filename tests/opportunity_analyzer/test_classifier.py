from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from agents.opportunity_analyzer.classifiers.opportunity_classifier import OpportunityClassifier
from agents.opportunity_analyzer.classifiers.settings import OpportunityAnalyzerSettings
from agents.opportunity_analyzer.schemas.models import (
    BudgetSource,
    OpportunityAssessment,
    OpportunityStatus,
    ProductionTenderRecord,
    RiskLevel,
)


ROOT = Path(__file__).resolve().parents[2]


def _settings() -> OpportunityAnalyzerSettings:
    scoring_path = ROOT / "configs" / "scoring.yaml"
    profile_path = ROOT / "agents" / "opportunity_analyzer" / "profiles" / "company_profile.yaml"
    scoring = OpportunityAnalyzerSettings.load_scoring_config(scoring_path)
    return OpportunityAnalyzerSettings(
        model="test-model",
        scoring=scoring,
        scoring_config_path=scoring_path,
        company_profile_path=profile_path,
    )


def _record(*, title: str, country: str = "Morocco", description: str = "test description") -> ProductionTenderRecord:
    now = datetime.now(timezone.utc)
    return ProductionTenderRecord(
        id=uuid4(),
        unique_key=str(uuid4()),
        source="unit-test",
        title=title,
        country=country,
        posting_date=now.date().isoformat(),
        deadline=date.today() + timedelta(days=30),
        url="https://example.com",
        description=description,
        external_id=None,
        staging_tender_id=uuid4(),
        gatekeeper_decision_id=None,
        created_at=now,
        updated_at=now,
    )


class _StubScorer:
    def __init__(self, assessment: OpportunityAssessment) -> None:
        self.assessment = assessment

    def score(self, _record: ProductionTenderRecord) -> OpportunityAssessment:
        return self.assessment


def test_hard_prefilter_rejects_bid_bond_above_profile_limit() -> None:
    classifier = OpportunityClassifier(settings=_settings(), scorer=_StubScorer(_base_assessment()))
    rec = _record(
        title="Urban development lot",
        description="Bid bond 7% is mandatory. Standard civil works.",
    )
    decision = classifier.classify(rec)
    assert decision.status == OpportunityStatus.NOT_FIT
    assert any("Bid bond above 5%" in b for b in decision.blockers)


def test_hard_prefilter_rejects_non_target_local_presence_requirement() -> None:
    classifier = OpportunityClassifier(settings=_settings(), scorer=_StubScorer(_base_assessment()))
    rec = _record(
        title="Municipal services contract",
        country="Spain",
        description="Mandatory local office and local tax registration prior to award.",
    )
    decision = classifier.classify(rec)
    assert decision.status == OpportunityStatus.NOT_FIT
    assert any("local presence" in b.lower() for b in decision.blockers)


def test_near_threshold_is_routed_to_review() -> None:
    assessment = _base_assessment(total=74.0, confidence=0.9, status=OpportunityStatus.GOOD_FIT)
    classifier = OpportunityClassifier(settings=_settings(), scorer=_StubScorer(assessment))
    rec = _record(title="Public transit optimization")
    decision = classifier.classify(rec)
    assert decision.status == OpportunityStatus.NEEDS_REVIEW


def _base_assessment(
    *,
    total: float = 83.0,
    confidence: float = 0.85,
    status: OpportunityStatus = OpportunityStatus.GOOD_FIT,
) -> OpportunityAssessment:
    return OpportunityAssessment(
        status=status,
        total_score=total,
        confidence_score=confidence,
        decision_reason="base assessment",
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
        strengths=["ok"],
        gaps=[],
        budget_source=BudgetSource.ESTIMATED,
        budget_eur=200000.0,
        budget_range_min_eur=100000.0,
        budget_range_max_eur=300000.0,
        budget_estimation_rationale="test",
    )
