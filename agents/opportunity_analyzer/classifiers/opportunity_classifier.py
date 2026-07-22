"""Opportunity classifier that applies LLM scoring plus policy guardrails."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from typing import Any

import yaml

from agents.opportunity_analyzer.classifiers.settings import (
    OpportunityAnalyzerSettings,
)
from agents.opportunity_analyzer.schemas.models import (
    OpportunityAssessment,
    OpportunityDecision,
    OpportunityStatus,
    ProductionTenderRecord,
    RiskLevel,
)
from agents.opportunity_analyzer.scorers.llm_semantic_scorer import LLMSemanticScorer


class OpportunityClassifier:
    """Run LLM-first scoring then enforce deterministic safety rules."""

    def __init__(
        self,
        settings: OpportunityAnalyzerSettings | None = None,
        scorer: LLMSemanticScorer | None = None,
    ) -> None:
        self.settings = settings or OpportunityAnalyzerSettings.from_env()
        self.scorer = scorer or LLMSemanticScorer(settings=self.settings)
        self.profile_policy = self._load_profile_policy(self.settings.company_profile_path)
        self.excluded_sector_terms = self.profile_policy["excluded_sector_terms"]
        self.target_countries = self.profile_policy["target_countries"]
        self.hard_blocker_phrases = self.profile_policy["hard_blocker_phrases"]

    def classify(self, record: ProductionTenderRecord | dict[str, Any]) -> OpportunityDecision:
        """Classify one production tender and return final auditable decision."""
        if isinstance(record, dict):
            record = ProductionTenderRecord.model_validate(record)

        prefilter_assessment = self._run_hard_prefilter(record)
        if prefilter_assessment is not None:
            final_assessment = prefilter_assessment
        else:
            assessment = self.scorer.score(record)
            final_assessment = self._apply_guardrails(record, assessment)

        return OpportunityDecision(
            production_tender_id=record.id,
            unique_key=record.unique_key,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
            **final_assessment.model_dump(),
        )

    def _run_hard_prefilter(self, record: ProductionTenderRecord) -> OpportunityAssessment | None:
        """Deterministic prefilter to suppress false-positive good_fit decisions."""
        haystack = self._haystack(record)
        blockers: list[str] = []
        blocker_evidence: dict[str, str] = {}

        excluded = self._find_excluded_sector(haystack)
        if excluded:
            blocker = f"Excluded sector matched: {excluded}"
            blockers.append(blocker)
            blocker_evidence[blocker] = f"Matched excluded sector term in tender text: '{excluded}'"

        if self._has_unlimited_liability(haystack):
            blocker = "Unlimited liability requirement detected"
            blockers.append(blocker)
            blocker_evidence[blocker] = "Detected 'unlimited' + 'liability' in tender text"

        bid_bond = self._extract_percent(haystack, "bid bond")
        if bid_bond is not None and bid_bond > 5.0:
            blocker = "Bid bond above 5% detected"
            blockers.append(blocker)
            blocker_evidence[blocker] = f"Detected bid bond percentage: {bid_bond}%"

        perf_bond = self._extract_percent(haystack, "performance bond")
        if perf_bond is not None and perf_bond > 15.0:
            blocker = "Performance bond above 15% detected"
            blockers.append(blocker)
            blocker_evidence[blocker] = f"Detected performance bond percentage: {perf_bond}%"

        if self._requires_local_presence(haystack):
            country_code = self._normalize_country_code(record.country)
            if country_code is not None and country_code not in self.target_countries:
                blocker = "Mandatory local presence in non-target country detected"
                blockers.append(blocker)
                blocker_evidence[blocker] = (
                    f"Local presence requirement found while country='{record.country}' "
                    f"(normalized={country_code}) is outside target_countries={sorted(self.target_countries)}"
                )

        for phrase in self.hard_blocker_phrases:
            if phrase and phrase in haystack:
                blocker = f"Hard blocker phrase matched: {phrase}"
                blockers.append(blocker)
                blocker_evidence[blocker] = f"Matched hard blocker phrase in tender text: '{phrase}'"

        if not blockers:
            return None

        unique_blockers = self._merge_unique(blockers)
        reason = "Deterministic hard-prefilter rejected tender: " + "; ".join(unique_blockers)

        return OpportunityAssessment(
            status=OpportunityStatus.NOT_FIT,
            total_score=0.0,
            confidence_score=0.95,
            decision_reason=reason,
            risk_level=RiskLevel.HIGH,
            score_breakdown={
                "domain_relevance": 0.0,
                "geography_fit": 0.0,
                "budget_fit": 0.0,
                "eligibility_fit": 0.0,
                "strategic_fit": 0.0,
            },
            blockers=unique_blockers,
            blocker_evidence=blocker_evidence,
            strengths=[],
            gaps=[],
            budget_source="unknown",
            budget_eur=None,
            budget_range_min_eur=None,
            budget_range_max_eur=None,
            budget_estimation_rationale="deterministic_hard_prefilter",
        )

    def _apply_guardrails(
        self,
        record: ProductionTenderRecord,
        assessment: OpportunityAssessment,
    ) -> OpportunityAssessment:
        cfg = self.settings.scoring
        if cfg is None:
            return assessment

        status = assessment.status
        override_reasons: list[str] = []
        haystack = self._haystack(record)
        strengths_output = list(assessment.strengths)
        score_breakdown_output = dict(assessment.score_breakdown)
        total_score_output = assessment.total_score
        excluded_sector_reason: str | None = None

        keyword_blockers = self._detect_keyword_blockers(haystack, cfg.risk.blocker_keywords)
        valid_llm_blockers, unsupported_llm_blockers, blocker_evidence = self._filter_evidenced_llm_blockers(
            assessment.blockers,
            haystack,
        )

        blockers = self._merge_unique(valid_llm_blockers, keyword_blockers)
        for keyword in keyword_blockers:
            blocker_evidence.setdefault(keyword, f"Matched blocker keyword in tender text: '{keyword}'")
        if unsupported_llm_blockers:
            override_reasons.append("Unsupported blocker claims were ignored due to missing evidence")

        # 1) Blockers first
        blocker_outcome_locked = False
        if cfg.rules.hard_filters_enabled and blockers:
            if cfg.rules.reject_if_any_blocker:
                status = OpportunityStatus.NOT_FIT
                blocker_outcome_locked = True
                override_reasons.append("Hard blocker(s) detected; auto-rejected by policy")
            else:
                status = OpportunityStatus.NEEDS_REVIEW
                override_reasons.append("Potential blocker(s) detected; routed to manual review")

        # 1.b) Consistency check: all-zero assessment + unsupported blockers => review only
        if (
            assessment.total_score == 0
            and assessment.confidence_score == 0
            and assessment.blockers
            and not blockers
        ):
            status = OpportunityStatus.NEEDS_REVIEW
            blocker_outcome_locked = False
            override_reasons.append("All-zero assessment with unsupported blockers; downgraded to manual review")

        # 1.c) Excluded sectors guardrail
        excluded_sector = self._find_excluded_sector(haystack)
        if excluded_sector:
            status = OpportunityStatus.NOT_FIT
            blocker_outcome_locked = True
            blockers = self._merge_unique(blockers, [f"Excluded sector matched: {excluded_sector}"])
            blocker_evidence[f"Excluded sector matched: {excluded_sector}"] = (
                f"Matched excluded sector term in tender text: '{excluded_sector}'"
            )
            override_reasons.append(f"Tender falls under excluded sector '{excluded_sector}'")
            excluded_sector_reason = (
                f"Excluded sector policy triggered: '{excluded_sector}'. Tender is not fit regardless of LLM score."
            )
            strengths_output = []
            score_breakdown_output["domain_relevance"] = min(score_breakdown_output.get("domain_relevance", 0.0), 20.0)
            score_breakdown_output["strategic_fit"] = min(score_breakdown_output.get("strategic_fit", 0.0), 20.0)
            total_score_output = round(
                score_breakdown_output.get("domain_relevance", 0.0) * cfg.weights.domain_relevance
                + score_breakdown_output.get("geography_fit", 0.0) * cfg.weights.geography_fit
                + score_breakdown_output.get("budget_fit", 0.0) * cfg.weights.budget_fit
                + score_breakdown_output.get("eligibility_fit", 0.0) * cfg.weights.eligibility_fit
                + score_breakdown_output.get("strategic_fit", 0.0) * cfg.weights.strategic_fit,
                2,
            )

        # 2) Confidence gate (unless blocked to NOT_FIT by policy)
        low_confidence = assessment.confidence_score < cfg.confidence.min_for_auto_decision
        if not blocker_outcome_locked and low_confidence:
            status = OpportunityStatus.NEEDS_REVIEW
            override_reasons.append(
                f"Confidence {assessment.confidence_score:.2f} below minimum "
                f"{cfg.confidence.min_for_auto_decision:.2f}"
            )

        # 3) Score thresholds (unless confidence already forced needs_review)
        if not blocker_outcome_locked and not low_confidence:
            status = self._status_from_score(total_score_output, cfg.thresholds)

        # 4) Boundary safety
        if not blocker_outcome_locked and self._is_near_threshold(total_score_output, cfg.thresholds, margin=3.0):
            status = OpportunityStatus.NEEDS_REVIEW
            override_reasons.append("Score is near decision threshold; manual review required")

        # 5) Deadline and minimal-data safety
        days_left = (record.deadline - date.today()).days
        if days_left < cfg.rules.deadline.reject_if_days_left_below:
            status = OpportunityStatus.NOT_FIT
            override_reasons.append(f"Tender deadline already invalid for bidding window (days_left={days_left})")
        elif days_left < cfg.rules.deadline.warning_if_days_left_below:
            if status is OpportunityStatus.GOOD_FIT:
                status = OpportunityStatus.NEEDS_REVIEW
            override_reasons.append(f"Tender deadline is urgent (days_left={days_left})")

        if cfg.rules.require_non_empty_description and not (record.description and record.description.strip()):
            if status is OpportunityStatus.GOOD_FIT:
                status = OpportunityStatus.NEEDS_REVIEW
            override_reasons.append("Missing tender description required by policy")

        risk_level = assessment.risk_level
        if blockers:
            risk_level = RiskLevel.HIGH
        elif risk_level is RiskLevel.HIGH:
            risk_level = RiskLevel.MEDIUM
            override_reasons.append("Risk normalized to medium because no evidenced blockers remain")

        decision_reason = assessment.decision_reason
        if excluded_sector_reason:
            decision_reason = excluded_sector_reason
        elif override_reasons:
            decision_reason = f"{'; '.join(override_reasons)}. Base reason: {assessment.decision_reason}"

        gaps = list(assessment.gaps)
        if low_confidence and "Low confidence assessment" not in gaps:
            gaps.append("Low confidence assessment")
        if days_left < cfg.rules.deadline.warning_if_days_left_below and "Short time to deadline" not in gaps:
            gaps.append("Short time to deadline")

        return OpportunityAssessment(
            status=status,
            total_score=total_score_output,
            confidence_score=assessment.confidence_score,
            decision_reason=decision_reason,
            risk_level=risk_level,
            score_breakdown=score_breakdown_output,
            blockers=blockers,
            blocker_evidence=blocker_evidence,
            strengths=strengths_output,
            gaps=gaps,
            budget_source=assessment.budget_source,
            budget_eur=assessment.budget_eur,
            budget_range_min_eur=assessment.budget_range_min_eur,
            budget_range_max_eur=assessment.budget_range_max_eur,
            budget_estimation_rationale=assessment.budget_estimation_rationale,
        )

    @staticmethod
    def _status_from_score(score: float, thresholds: Any) -> OpportunityStatus:
        if score >= thresholds.good_fit_min:
            return OpportunityStatus.GOOD_FIT
        if score >= thresholds.needs_review_min:
            return OpportunityStatus.NEEDS_REVIEW
        return OpportunityStatus.NOT_FIT

    @staticmethod
    def _is_near_threshold(score: float, thresholds: Any, margin: float = 3.0) -> bool:
        return (
            abs(score - thresholds.good_fit_min) <= margin
            or abs(score - thresholds.needs_review_min) <= margin
        )

    @staticmethod
    def _detect_keyword_blockers(haystack: str, blocker_keywords: list[str]) -> list[str]:
        if not blocker_keywords:
            return []

        found: list[str] = []
        for keyword in blocker_keywords:
            token = keyword.strip().lower()
            if token and token in haystack:
                found.append(keyword)
        return found

    @staticmethod
    def _filter_evidenced_llm_blockers(blockers: list[str], haystack: str) -> tuple[list[str], list[str], dict[str, str]]:
        valid: list[str] = []
        unsupported: list[str] = []
        evidence: dict[str, str] = {}
        for blocker in blockers:
            token = blocker.strip()
            if not token:
                continue
            token_lower = token.lower()
            if token_lower in haystack:
                valid.append(token)
                evidence[token] = f"Matched blocker phrase in tender text: '{token}'"
            else:
                unsupported.append(token)
        return valid, unsupported, evidence

    @staticmethod
    def _haystack(record: ProductionTenderRecord) -> str:
        return " ".join(
            [
                (record.title or ""),
                (record.description or ""),
                (record.url or ""),
                (record.source or ""),
            ]
        ).lower()

    @staticmethod
    def _extract_percent(haystack: str, prefix: str) -> float | None:
        pattern = re.compile(rf"{re.escape(prefix)}[^%\n\r]{{0,40}}(\d{{1,2}}(?:\.\d+)?)\s*%")
        match = pattern.search(haystack)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _has_unlimited_liability(haystack: str) -> bool:
        return "unlimited" in haystack and "liability" in haystack

    @staticmethod
    def _requires_local_presence(haystack: str) -> bool:
        local_markers = [
            "mandatory local office",
            "mandatory local registration",
            "local company registration",
            "local state registration",
            "prior to award",
            "prior to proposal submission",
            "local tax registration",
        ]
        return any(marker in haystack for marker in local_markers)

    @staticmethod
    def _load_profile_policy(profile_path: Path) -> dict[str, Any]:
        if not profile_path.exists():
            return {
                "excluded_sector_terms": [],
                "target_countries": set(),
                "hard_blocker_phrases": [],
            }
        try:
            raw = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {
                "excluded_sector_terms": [],
                "target_countries": set(),
                "hard_blocker_phrases": [],
            }

        strategy = raw.get("strategy", {}) if isinstance(raw, dict) else {}
        excluded = strategy.get("excluded_sectors", []) if isinstance(strategy, dict) else []
        target_countries = strategy.get("target_countries", []) if isinstance(strategy, dict) else []
        eligibility = raw.get("eligibility", {}) if isinstance(raw, dict) else {}
        hard_blockers = eligibility.get("hard_blockers", []) if isinstance(eligibility, dict) else []

        base_terms = [str(x).strip().lower() for x in excluded if str(x).strip()]
        expanded = set(base_terms)
        synonym_map = {
            "construction": [
                "civil works",
                "construction work",
                "infrastructure work",
                "public lighting",
                "road works",
                "architectural study",
                "building rehabilitation",
                "greening project",
                "corridor development",
            ],
            "heavy industry": [
                "industrial plant",
                "factory expansion",
                "heavy equipment installation",
                "mining infrastructure",
            ],
        }
        for term in base_terms:
            for key, synonyms in synonym_map.items():
                if key in term:
                    expanded.update(s.lower() for s in synonyms)
        return {
            "excluded_sector_terms": sorted(expanded),
            "target_countries": {str(c).strip().upper() for c in target_countries if str(c).strip()},
            "hard_blocker_phrases": [str(x).strip().lower() for x in hard_blockers if str(x).strip()],
        }

    @staticmethod
    def _normalize_country_code(country: str | None) -> str | None:
        if not country:
            return None
        raw = country.strip().lower()
        alias = {
            "tn": "TN",
            "tunisia": "TN",
            "fr": "FR",
            "france": "FR",
            "ma": "MA",
            "morocco": "MA",
            "maroc": "MA",
        }
        return alias.get(raw, country.strip().upper())

    def _find_excluded_sector(self, haystack: str) -> str | None:
        for term in self.excluded_sector_terms:
            if term and term in haystack:
                return term
        return None

    @staticmethod
    def _merge_unique(*lists: list[str]) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []
        for values in lists:
            for value in values:
                item = value.strip()
                if not item:
                    continue
                norm = item.lower()
                if norm in seen:
                    continue
                seen.add(norm)
                merged.append(item)
        return merged
