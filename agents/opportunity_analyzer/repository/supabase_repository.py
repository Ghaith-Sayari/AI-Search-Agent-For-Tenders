"""
Thin persistence layer. Deliberately minimal -- the analysis pipeline
should work fully in-memory without this, so it's easy to test and so a
DB outage doesn't block analysis, only storage of results.
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
            logger.warning("No Supabase client configured; skipping persistence for %s",
                            analysis.opportunity_id)
            return

        record = {
            "opportunity_id": analysis.opportunity_id,
            "profile_id": analysis.profile_id,
            "total_score": analysis.total_score,
            "decision": analysis.decision.value,
            "reasoning": analysis.reasoning,
            "low_confidence": analysis.low_confidence,
            "signals": [asdict(s) for s in analysis.signals],
        }
        self.client.table("opportunity_analyses").insert(record).execute()

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
