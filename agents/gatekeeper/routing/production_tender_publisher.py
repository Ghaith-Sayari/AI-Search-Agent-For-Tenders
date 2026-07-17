"""Publish approved staging tenders to the production tender table."""

from typing import Any
from uuid import UUID

from agents.gatekeeper.schemas import (
    GatekeeperDecision,
    GatekeeperStatus,
    RawTenderStagingRecord,
)
from db.client import get_client


class ProductionTenderPublisher:
    """Copies only Gatekeeper-approved staging records into production."""

    def __init__(self, table_name: str = "production_tender") -> None:
        self.table_name = table_name

    def publish(
        self,
        record: RawTenderStagingRecord,
        decision: GatekeeperDecision,
        gatekeeper_decision_id: UUID | str | None = None,
    ) -> dict[str, Any]:
        """Upsert one approved tender and return the production row."""
        if decision.status is not GatekeeperStatus.APPROVED:
            raise ValueError("Only Gatekeeper decisions with status 'approved' can be published")
        if decision.staging_tender_id != record.id:
            raise ValueError("The decision does not belong to the supplied staging record")

        payload = {
            "unique_key": record.unique_key,
            "source": record.source,
            "title": record.title,
            "country": record.country,
            "posting_date": record.posting_date,
            "deadline": decision.extracted_deadline.isoformat()
            if decision.extracted_deadline
            else None,
            "url": record.url,
            "description": decision.cleaned_description,
            "external_id": record.external_id,
            "staging_tender_id": str(record.id),
            "gatekeeper_decision_id": str(gatekeeper_decision_id)
            if gatekeeper_decision_id
            else None,
        }

        response = (
            get_client()
            .table(self.table_name)
            .upsert(payload, on_conflict="unique_key")
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the published production tender")
        return response.data[0]
