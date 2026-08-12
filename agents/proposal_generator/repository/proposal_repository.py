from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agents.proposal_generator.models.proposal_output import ProposalOutput
from db.client import get_client


class ProposalRepository:
    def __init__(self, table_name: str = "generated_proposal", bucket_name: str = "proposal-files", client=None) -> None:
        self.table_name = table_name
        self.bucket_name = bucket_name
        self.client = client or get_client()

    def ensure_bucket(self, public: bool = False) -> None:
        """Best-effort bucket creation. No-op when already exists."""
        try:
            buckets = self.client.storage.list_buckets()
            exists = any(getattr(b, "name", None) == self.bucket_name or (isinstance(b, dict) and b.get("name") == self.bucket_name) for b in (buckets or []))
            if exists:
                return
            self.client.storage.create_bucket(self.bucket_name, options={"public": public})
        except Exception:
            # Bucket may already exist or API may be restricted in this environment.
            # SQL migration is the source of truth; runtime creation is only convenience.
            return

    def save_proposal(self, output: ProposalOutput, markdown_text: str) -> dict[str, Any]:
        payload = {
            "tender_external_id": output.tender_external_id,
            "profile_name": output.profile_name,
            "decision": output.decision,
            "total_score": output.total_score,
            "confidence_score": output.confidence_score,
            "executive_summary": output.executive_summary,
            "sections": [
                {
                    "key": s.key,
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "requirement_ids": s.requirement_ids,
                }
                for s in output.sections
            ],
            "compliance_issues": [
                {
                    "requirement_id": i.requirement_id,
                    "message": i.message,
                    "severity": i.severity,
                    "section_key": i.section_key,
                }
                for i in output.compliance_issues
            ],
            "metadata": output.metadata,
            "generated_at": output.generated_at.isoformat(),
            "markdown": markdown_text,
        }

        response = self.client.table(self.table_name).insert(payload).execute()
        if not response.data:
            raise RuntimeError("Supabase insert returned no row for generated proposal")
        return response.data[0]

    def upload_artifacts(self, proposal_row: dict[str, Any], output: ProposalOutput, markdown_text: str) -> dict[str, str]:
        """Upload JSON + markdown artifacts to Supabase Storage."""
        self.ensure_bucket(public=False)

        proposal_id = str(proposal_row.get("id") or "unknown")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        base_prefix = f"{output.profile_name.strip().replace(' ', '_')}/{proposal_id}/{stamp}"
        md_path = f"{base_prefix}/proposal.md"
        json_path = f"{base_prefix}/proposal.json"

        json_payload = {
            "proposal": proposal_row,
            "sections": payload_sections(output),
            "compliance_issues": payload_issues(output),
            "metadata": output.metadata,
        }

        self.client.storage.from_(self.bucket_name).upload(
            path=md_path,
            file=markdown_text.encode("utf-8"),
            file_options={"content-type": "text/markdown"},
        )
        self.client.storage.from_(self.bucket_name).upload(
            path=json_path,
            file=json.dumps(json_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_options={"content-type": "application/json"},
        )

        return {
            "bucket": self.bucket_name,
            "markdown_path": md_path,
            "json_path": json_path,
        }


def payload_sections(output: ProposalOutput) -> list[dict[str, Any]]:
    return [
        {
            "key": s.key,
            "title": s.title,
            "content": s.content,
            "order": s.order,
            "requirement_ids": s.requirement_ids,
        }
        for s in output.sections
    ]


def payload_issues(output: ProposalOutput) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": i.requirement_id,
            "message": i.message,
            "severity": i.severity,
            "section_key": i.section_key,
        }
        for i in output.compliance_issues
    ]
