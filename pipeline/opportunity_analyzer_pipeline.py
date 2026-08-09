"""Pipeline runner for the Opportunity Analyzer agent."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.opportunity_analyzer.audit.analysis_repository import OpportunityAnalysisRepository
from agents.opportunity_analyzer.classifiers.opportunity_classifier import OpportunityClassifier
from agents.opportunity_analyzer.classifiers.settings import OpportunityAnalyzerSettings
from agents.opportunity_analyzer.schemas.models import OpportunityStatus, ProductionTenderRecord
from db.client import get_client

logger = logging.getLogger(__name__)


class OpportunityAnalyzerPipeline:
    """Fetch production tenders, classify them, and persist analysis outcomes."""

    def __init__(
        self,
        classifier: OpportunityClassifier | None = None,
        source_table: str | None = None,
        audit_table: str | None = None,
    ) -> None:
        self.classifier = classifier or OpportunityClassifier()
        self.settings: OpportunityAnalyzerSettings = self.classifier.settings
        self.source_table = source_table or self.settings.source_table
        self.audit_table = audit_table or self.settings.audit_table
        self.client = get_client()
        self.audit_repository = OpportunityAnalysisRepository(table_name=self.audit_table)

    def fetch_source_records(self, limit: Optional[int] = None, offset: int = 0) -> List[dict[str, Any]]:
        """Fetch production tenders ordered by newest first."""
        query = self.client.table(self.source_table).select("*").order("created_at", desc=True)
        if limit is not None:
            query = query.range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []

    def _build_record(self, raw: dict[str, Any]) -> ProductionTenderRecord:
        return ProductionTenderRecord.model_validate(raw)

    def run(self, limit: Optional[int] = None, continue_on_error: bool = True) -> Dict[str, Any]:
        """Run the analyzer and return a summary report."""
        logger.info(
            "Starting OpportunityAnalyzerPipeline. Source=%s Audit=%s Policy=%s",
            self.source_table,
            self.audit_table,
            self.settings.policy_version,
        )

        processed_keys = self.audit_repository.get_processed_keys(self.settings.policy_version)
        raw_records = self.fetch_source_records(limit=limit)
        if not raw_records:
            return {
                "total_fetched": 0,
                "processed": 0,
                "skipped": 0,
                "errors": 0,
                "good_fit_count": 0,
                "needs_review_count": 0,
                "not_fit_count": 0,
                "failed_count": 0,
                "decisions": [],
            }

        unprocessed: list[dict[str, Any]] = []
        skipped_keys: list[str] = []
        for raw in raw_records:
            key = raw.get("unique_key")
            if key and key in processed_keys:
                skipped_keys.append(key)
                continue
            unprocessed.append(raw)

        decisions = []
        errors = []
        saved_count = 0
        save_errors = []

        counts = {
            OpportunityStatus.GOOD_FIT.value: 0,
            OpportunityStatus.NEEDS_REVIEW.value: 0,
            OpportunityStatus.NOT_FIT.value: 0,
            OpportunityStatus.FAILED.value: 0,
        }

        for idx, raw in enumerate(unprocessed, start=1):
            unique_key = raw.get("unique_key", f"item-{idx}")
            try:
                record = self._build_record(raw)
                decision = self.classifier.classify(record)
                decisions.append(decision)
                counts[decision.status.value] += 1

                try:
                    self.audit_repository.save(decision)
                    saved_count += 1
                except Exception as save_exc:
                    if not continue_on_error:
                        raise
                    save_errors.append({"unique_key": unique_key, "error": str(save_exc)})
                    logger.error("Failed to save analysis for %s: %s", unique_key, save_exc)

                logger.info(
                    "[%d/%d] %s -> %s (score=%.2f, confidence=%.2f)",
                    idx,
                    len(unprocessed),
                    decision.unique_key,
                    decision.status.value,
                    decision.total_score,
                    decision.confidence_score,
                )
            except Exception as exc:
                if not continue_on_error:
                    raise
                errors.append(
                    {
                        "index": idx,
                        "unique_key": unique_key,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    }
                )
                logger.error("[%d/%d] %s -> ERROR: %s", idx, len(unprocessed), unique_key, exc)

        recommendations = []
        ranking_error: str | None = None
        if decisions:
            try:
                recommendations = self.classifier._rank_decisions(decisions)
            except Exception as rank_exc:
                ranking_error = str(rank_exc)
                logger.error("Failed to rank opportunities: %s", rank_exc)

        return {
            "total_fetched": len(raw_records),
            "skipped": len(skipped_keys),
            "skipped_keys": skipped_keys,
            "processed": len(decisions),
            "errors": len(errors),
            "error_details": errors,
            "saved_audit": saved_count,
            "save_errors": len(save_errors),
            "save_error_details": save_errors,
            "good_fit_count": counts[OpportunityStatus.GOOD_FIT.value],
            "needs_review_count": counts[OpportunityStatus.NEEDS_REVIEW.value],
            "not_fit_count": counts[OpportunityStatus.NOT_FIT.value],
            "failed_count": counts[OpportunityStatus.FAILED.value],
            "decisions": decisions,
            "recommended_count": len(recommendations),
            "recommended_decisions": recommendations,
            "ranking_error": ranking_error,
        }
