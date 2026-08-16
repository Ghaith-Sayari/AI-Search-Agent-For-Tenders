"""Data access for company profile settings."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from db.client import get_client

_MEMORY_PROFILE: dict[str, Any] = {
    "id": "default",
    "name": "Default Organization",
    "description": "",
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
        self._unsupported_columns: set[str] = set()

    def _profiles_table(self):
        """
        Resolve public.profiles in a supabase-py-version-safe way.
        - Newer clients may expose `.schema("public").table(...)`
        - Older clients only expose `.table(...)` (defaults to public schema)
        """
        schema_method = getattr(self.client, "schema", None)
        if callable(schema_method):
            try:
                return schema_method("public").table(self.table_name)
            except Exception:
                # Fallback to default behavior below.
                pass
        return self.client.table(self.table_name)

    def get(self) -> dict[str, Any]:
        try:
            rows = (
                self._profiles_table()
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
                "id": str(row.get("id") or self.default_id),
                "name": str(row.get("name") or _MEMORY_PROFILE["name"]),
                "description": str(row.get("description") or ""),
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
        profile_id = str(payload.get("id") or self.default_id)
        db_payload: dict[str, Any] = {
            "id": profile_id,
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
            "description": payload.get("description"),
        }
        for col in list(self._unsupported_columns):
            db_payload.pop(col, None)

        # Retry when schema-cache errors indicate a missing column.
        # Keep removing unsupported columns until we either succeed or hit a non-schema error.
        max_attempts = len(db_payload) + 2
        last_exc: Exception | None = None
        for _attempt in range(max_attempts):
            try:
                _ = (
                    self._profiles_table()
                    .upsert(db_payload, on_conflict="id")
                    .execute()
                )
                break
            except Exception as exc:
                last_exc = exc
                msg = str(exc)
                m = re.search(r"Could not find the '([^']+)' column", msg)
                missing_col = m.group(1) if m else None
                if missing_col and missing_col in db_payload:
                    self._unsupported_columns.add(missing_col)
                    db_payload.pop(missing_col, None)
                    continue
                # Do not silently fallback: caller needs to know profile was NOT persisted.
                raise RuntimeError(f"Failed to persist company profile in public.{self.table_name}: {exc}") from exc
        else:
            raise RuntimeError(f"Failed to persist company profile in public.{self.table_name}: {last_exc}")

        payload["id"] = profile_id
        _MEMORY_PROFILE.update(payload)
        rows = (
            self._profiles_table()
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            row = rows[0]
            return {
                "id": str(row.get("id") or profile_id),
                "name": str(row.get("name") or _MEMORY_PROFILE["name"]),
                "description": str(row.get("description") or ""),
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
        return deepcopy(_MEMORY_PROFILE)
