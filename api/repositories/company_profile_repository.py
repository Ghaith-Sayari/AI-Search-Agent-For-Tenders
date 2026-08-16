"""Data access for company profile settings."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from db.client import get_client

_MEMORY_PROFILE: dict[str, Any] = {
    "name": "Default Organization",
    "primarySector": "",
    "subSectors": [],
    "coreServices": [],
    "targetCountries": [],
    "certifications": [],
    "minContractValueEur": None,
    "maxContractValueEur": None,
    "gatekeeperMinScore": 50.0,
    "autoApproveThreshold": 75.0,
}


class CompanyProfileRepository:
    """Repository with DB-first strategy and in-memory fallback.

    DB mapping uses `profiles` table default row id='default'.
    """

    def __init__(self) -> None:
        self.client = get_client()
        self.table_name = "profiles"
        self.default_id = "default"

    def get(self) -> dict[str, Any]:
        try:
            rows = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", self.default_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if not rows:
                return deepcopy(_MEMORY_PROFILE)
            row = rows[0]
            return {
                "name": str(row.get("name") or _MEMORY_PROFILE["name"]),
                "primarySector": str(row.get("primary_sector") or ""),
                "subSectors": row.get("sectors") if isinstance(row.get("sectors"), list) else [],
                "coreServices": row.get("keywords") if isinstance(row.get("keywords"), list) else [],
                "targetCountries": row.get("locations") if isinstance(row.get("locations"), list) else [],
                "certifications": row.get("certifications") if isinstance(row.get("certifications"), list) else [],
                "minContractValueEur": row.get("min_budget"),
                "maxContractValueEur": row.get("max_budget"),
                "gatekeeperMinScore": float(row.get("gatekeeper_min_score") or _MEMORY_PROFILE["gatekeeperMinScore"]),
                "autoApproveThreshold": float(
                    row.get("auto_approve_threshold") or _MEMORY_PROFILE["autoApproveThreshold"]
                ),
            }
        except Exception:
            return deepcopy(_MEMORY_PROFILE)

    def put(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            db_payload = {
                "id": self.default_id,
                "name": payload.get("name"),
                "primary_sector": payload.get("primarySector"),
                "sectors": payload.get("subSectors"),
                "keywords": payload.get("coreServices"),
                "locations": payload.get("targetCountries"),
                "certifications": payload.get("certifications"),
                "min_budget": payload.get("minContractValueEur"),
                "max_budget": payload.get("maxContractValueEur"),
                "gatekeeper_min_score": payload.get("gatekeeperMinScore"),
                "auto_approve_threshold": payload.get("autoApproveThreshold"),
                "description": "Company profile settings",
            }
            _ = (
                self.client.table(self.table_name)
                .upsert(db_payload, on_conflict="id")
                .execute()
            )
        except Exception:
            # fallback to memory only
            pass

        _MEMORY_PROFILE.update(payload)
        return deepcopy(_MEMORY_PROFILE)
