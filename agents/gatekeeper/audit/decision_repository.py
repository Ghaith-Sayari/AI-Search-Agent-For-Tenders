"""Write Gatekeeper decisions to the Supabase audit table."""

from typing import Any

from agents.gatekeeper.schemas import GatekeeperDecision
from db.client import get_client


class GatekeeperDecisionRepository:
    """Stores every decision without modifying the original staging record."""

    def __init__(self, table_name: str = "gatekeeper_decisions") -> None:
        self.table_name = table_name

    def save(self, decision: GatekeeperDecision) -> dict[str, Any]:
        """Upsert one audit event and return the saved row."""
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
            raise RuntimeError("Supabase did not return the saved Gatekeeper decision")
        return response.data[0]
