"""Write Gatekeeper dead-letter records to Supabase."""

from typing import Any

from db.client import get_client


class GatekeeperDeadLetterRepository:
    """Stores failed Gatekeeper processing events for replay and triage."""

    def __init__(self, table_name: str = "gatekeeper_dead_letter") -> None:
        self.table_name = table_name

    def save(self, item: dict[str, Any]) -> dict[str, Any]:
        """Upsert one dead-letter event and return the saved row."""
        response = (
            get_client()
            .table(self.table_name)
            .upsert(
                item,
                on_conflict="unique_key,policy_version",
            )
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the saved dead-letter event")
        return response.data[0]

