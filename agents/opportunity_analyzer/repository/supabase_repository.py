"""
Thin persistence layer for the Opportunity Analyzer.

Persistence contract: analyzed_tender only.
"""

from dataclasses import asdict

from agents.opportunity_analyzer.models.analysis import Analysis
from agents.opportunity_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseRepository:
    def __init__(self, client=None):
        """
        `client` is expected to be a `supabase.Client` instance
        (from `supabase-py`). Passed in rather than constructed here so
        tests can inject a fake/mock client.
        """
        self.client = client

    def save_analysis(self, analysis: Analysis) -> None:
        if self.client is None:
            logger.warning(
                "No Supabase client configured; skipping persistence for %s",
                analysis.opportunity_id,
            )
            return

        total_weight = sum(max(0.0, s.weight) for s in analysis.signals) or 1.0
        confidence_score = sum(
            max(0.0, s.weight) * max(0.0, min(1.0, s.confidence))
            for s in analysis.signals
        ) / total_weight

        record = {
            "production_tender_id": analysis.opportunity_id,
            "unique_key": analysis.opportunity_id,
            "profile_id": analysis.profile_id,
            "decision": analysis.decision.value,
            "total_score": round(analysis.total_score * 100.0, 2),
            "total_score_normalized": round(analysis.total_score, 6),
            "confidence_score": round(confidence_score, 6),
            "low_confidence": analysis.low_confidence,
            "decision_reason": analysis.reasoning or "Scored by Opportunity Analyzer",
            "llm_status": "unknown",
            "llm_error": None,
            "matched_keywords": [],
            "location_match_type": "unknown",
            "signals": [asdict(s) for s in analysis.signals],
            "policy_version": "1.0",
            "agent_version": "1.0",
        }
        self.client.table("analyzed_tender").upsert(
            record,
            on_conflict="unique_key,profile_id,policy_version",
        ).execute()

    def get_profile(self, profile_id: str) -> dict | None:
        if self.client is None:
            return None
        result = (
            self.client.table("profiles")
            .select("*")
            .eq("id", profile_id)
            .single()
            .execute()
        )
        return result.data
