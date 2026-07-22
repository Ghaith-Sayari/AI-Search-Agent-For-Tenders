"""Opportunity classifier that applies LLM scoring plus policy guardrails."""

from __future__ import annotations

from datetime import date
from pathlib import Path
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
        self.excluded_sector_terms = self._load_excluded_sector_terms(self.settings.company_profile_path)

    def classify(self, record: ProductionTenderRecord | dict[str, Any]) -> OpportunityDecision:
        """Classify one production tender and return final auditable decision."""
        if isinstance(record, dict):
            record = ProductionTenderRecord.model_validate(record)

        assessment = self.scorer.score(record)
        final_assessment = self._apply_guardrails(record, assessment)

        return OpportunityDecision(
            production_tender_id=record.id,
            unique_key=record.unique_key,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
            **final_assessment.model_dump(),
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
            status = self._status_from_score(assessment.total_score, cfg.thresholds)

        # 4) Boundary safety
        if not blocker_outcome_locked and self._is_near_threshold(assessment.total_score, cfg.thresholds, margin=3.0):
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
        if override_reasons:
            decision_reason = f"{'; '.join(override_reasons)}. Base reason: {assessment.decision_reason}"

        gaps = list(assessment.gaps)
        if low_confidence and "Low confidence assessment" not in gaps:
            gaps.append("Low confidence assessment")
        if days_left < cfg.rules.deadline.warning_if_days_left_below and "Short time to deadline" not in gaps:
            gaps.append("Short time to deadline")

        return OpportunityAssessment(
            status=status,
            total_score=assessment.total_score,
            confidence_score=assessment.confidence_score,
            decision_reason=decision_reason,
            risk_level=risk_level,
            score_breakdown=assessment.score_breakdown,
            blockers=blockers,
            blocker_evidence=blocker_evidence,
            strengths=assessment.strengths,
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
    def _load_excluded_sector_terms(profile_path: Path) -> list[str]:
        if not profile_path.exists():
            return []
        try:
            raw = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return []
        strategy = raw.get("strategy", {}) if isinstance(raw, dict) else {}
        excluded = strategy.get("excluded_sectors", []) if isinstance(strategy, dict) else []
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
        return sorted(expanded)

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
