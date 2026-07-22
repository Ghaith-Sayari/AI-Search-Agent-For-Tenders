"""Write Opportunity Analyzer decisions to the Supabase audit table."""

from __future__ import annotations

from typing import Any

from agents.opportunity_analyzer.schemas.models import OpportunityDecision
from db.client import get_client


class OpportunityAnalysisRepository:
    """Stores every analyzer decision for auditability and replay."""

    def __init__(self, table_name: str = "opportunity_analysis") -> None:
        self.table_name = table_name

    def save(self, decision: OpportunityDecision) -> dict[str, Any]:
        """Upsert one analysis event and return the saved row."""
        response = (
            get_client()
            .table(self.table_name)
            .upsert(
                decision.model_dump(mode="json"),
                on_conflict="unique_key,policy_version",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError("Supabase did not return the saved Opportunity Analyzer decision")
        return response.data[0]

    def get_processed_keys(self, policy_version: str) -> set[str]:
        """Return unique keys already analyzed for the supplied policy version."""
        response = (
            get_client()
            .table(self.table_name)
            .select("unique_key")
            .eq("policy_version", policy_version)
            .execute()
        )
        if not response.data:
            return set()
        return {row["unique_key"] for row in response.data if row.get("unique_key")}
