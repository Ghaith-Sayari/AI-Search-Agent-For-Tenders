"""Data access for proposal endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from db.client import get_client


class ProposalApiRepository:
    def __init__(self) -> None:
        self.client = get_client()
        self.table = "generated_proposal"
        self.bucket = "proposal-files"

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        return (
            self.client.table(self.table)
            .select("*")
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )

    def get(self, proposal_id: str) -> dict[str, Any] | None:
        rows = (
            self.client.table(self.table)
            .select("*")
            .eq("id", proposal_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def create_draft(
        self,
        *,
        opportunity_row: dict[str, Any],
        profile_row: dict[str, Any] | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        metadata = {
            "status": "DRAFT",
            "opportunity_id": payload.get("opportunityId"),
            "analyzed_tender_id": opportunity_row.get("id"),
            "tender_title": payload.get("proposalTitle") or opportunity_row.get("title"),
            "country": opportunity_row.get("country"),
            "source": opportunity_row.get("source"),
            "deadline": opportunity_row.get("deadline"),
            "company_profile_id": payload.get("companyProfileId"),
            "company_profile_name": (profile_row or {}).get("name"),
            "language": payload.get("language"),
            "proposal_type": payload.get("proposalType"),
            "tone": payload.get("tone"),
            "additional_instructions": payload.get("additionalInstructions"),
            "created_via": "api",
        }
        db_payload = {
            "tender_external_id": str(opportunity_row.get("external_id") or payload.get("opportunityId")),
            "profile_name": str((profile_row or {}).get("name") or "Unknown profile"),
            "decision": "review",
            "total_score": 0.0,
            "confidence_score": 0.0,
            "executive_summary": "",
            "sections": [],
            "compliance_issues": [],
            "metadata": metadata,
            "markdown": "",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        rows = self.client.table(self.table).insert(db_payload).execute().data or []
        if not rows:
            raise RuntimeError("Failed to create proposal draft")
        return rows[0]

    def update(self, proposal_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get(proposal_id)
        if not current:
            return None

        update_payload: dict[str, Any] = {}
        if "sections" in patch:
            update_payload["sections"] = patch["sections"]
        if "executive_summary" in patch:
            update_payload["executive_summary"] = patch["executive_summary"]
        if "executiveSummary" in patch:
            update_payload["executive_summary"] = patch["executiveSummary"]
        if "decision" in patch:
            update_payload["decision"] = patch["decision"]
        if "total_score" in patch:
            update_payload["total_score"] = patch["total_score"]
        if "overallScore" in patch and patch["overallScore"] is not None:
            update_payload["total_score"] = float(patch["overallScore"]) / 100.0
        if "confidence_score" in patch:
            update_payload["confidence_score"] = patch["confidence_score"]
        if "markdown" in patch:
            update_payload["markdown"] = patch["markdown"]

        if "metadata" in patch and isinstance(patch["metadata"], dict):
            merged_meta = dict(current.get("metadata") if isinstance(current.get("metadata"), dict) else {})
            merged_meta.update(patch["metadata"])
            update_payload["metadata"] = merged_meta
        elif any(
            key in patch
            for key in (
                "status",
                "config",
                "opportunityTitle",
                "country",
                "source",
                "deadline",
            )
        ):
            merged_meta = dict(current.get("metadata") if isinstance(current.get("metadata"), dict) else {})
            if "status" in patch:
                merged_meta["status"] = patch["status"]
            if "config" in patch and isinstance(patch["config"], dict):
                cfg = patch["config"]
                merged_meta["proposal_title"] = cfg.get("title", merged_meta.get("proposal_title"))
                merged_meta["company_profile_id"] = cfg.get("companyProfileId", merged_meta.get("company_profile_id"))
                merged_meta["company_profile_name"] = cfg.get("companyProfileName", merged_meta.get("company_profile_name"))
                merged_meta["language"] = cfg.get("language", merged_meta.get("language"))
                merged_meta["proposal_type"] = cfg.get("proposalType", merged_meta.get("proposal_type"))
                merged_meta["tone"] = cfg.get("tone", merged_meta.get("tone"))
                merged_meta["additional_instructions"] = cfg.get(
                    "additionalInstructions", merged_meta.get("additional_instructions")
                )
            for key, meta_key in (
                ("opportunityTitle", "tender_title"),
                ("country", "country"),
                ("source", "source"),
                ("deadline", "deadline"),
            ):
                if key in patch:
                    merged_meta[meta_key] = patch[key]
            update_payload["metadata"] = merged_meta

        # Normalize sections shape from API patch schema to DB sections schema.
        if "sections" in update_payload and isinstance(update_payload["sections"], list):
            normalized: list[dict[str, Any]] = []
            for idx, s in enumerate(update_payload["sections"]):
                if not isinstance(s, dict):
                    continue
                sid = str(s.get("id") or s.get("key") or f"section-{idx+1}")
                normalized.append(
                    {
                        "id": sid,
                        "key": sid,
                        "title": s.get("title") or sid,
                        "content": s.get("content") or "",
                        "status": s.get("status") or "GENERATED",
                        "lastUpdated": s.get("lastUpdated") or datetime.now(timezone.utc).isoformat(),
                        "order": idx + 1,
                        "requirement_ids": s.get("requirement_ids") if isinstance(s.get("requirement_ids"), list) else [],
                    }
                )
            update_payload["sections"] = normalized

        rows = (
            self.client.table(self.table)
            .update(update_payload)
            .eq("id", proposal_id)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def get_analyzed_opportunity(self, opportunity_id: str) -> dict[str, Any] | None:
        rows = (
            self.client.table("analyzed_tender")
            .select("*")
            .eq("id", opportunity_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            return rows[0]
        rows = (
            self.client.table("analyzed_tender")
            .select("*")
            .or_(f"production_tender_id.eq.{opportunity_id},unique_key.eq.{opportunity_id}")
            .order("processed_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        rows = (
            self.client.table("profiles")
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def upload_export(self, *, proposal_id: str, fmt: str, content: bytes) -> dict[str, str]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ext = {"pdf": "pdf", "docx": "docx", "markdown": "md"}.get(fmt, "txt")
        file_name = f"proposal_{proposal_id}_{ts}.{ext}"
        path = f"exports/{proposal_id}/{file_name}"

        content_type = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "markdown": "text/markdown",
        }.get(fmt, "application/octet-stream")

        self.client.storage.from_(self.bucket).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type},
        )
        signed = self.client.storage.from_(self.bucket).create_signed_url(path, 3600)
        file_url = signed.get("signedURL") if isinstance(signed, dict) else ""
        return {"fileName": file_name, "fileUrl": file_url}

    @staticmethod
    def build_placeholder_section(action: str, section_id: str, previous: str = "") -> str:
        prompt = {
            "Regenerate": "Regenerated section content based on latest requirements.",
            "Improve": "Improved clarity, structure, and persuasiveness of this section.",
            "Shorten": "Condensed this section while preserving key points.",
            "Expand": "Expanded this section with additional detail and evidence.",
        }.get(action, "Updated section content.")
        if previous:
            return f"{previous}\n\n[{prompt}]"
        return f"[{section_id}] {prompt}"
