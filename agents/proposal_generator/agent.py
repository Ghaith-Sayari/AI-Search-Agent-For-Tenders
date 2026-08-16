"""End-to-end Proposal Generator agent runner."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agents.proposal_generator.models.proposal_input import (
    CompanyProfileInput,
    ProposalInput,
    TenderData,
)
from agents.proposal_generator.pipeline.build_outline import build_outline
from agents.proposal_generator.pipeline.compliance_review import (
    compliance_pass_rate,
    review_compliance,
)
from agents.proposal_generator.pipeline.draft_sections import draft_sections_with_llm
from agents.proposal_generator.pipeline.export import build_export_bundle, build_proposal_output
from agents.proposal_generator.pipeline.prepare_context import prepare_context
from agents.proposal_generator.pipeline.score_proposal import score_proposal
from agents.proposal_generator.repository.proposal_repository import ProposalRepository
from db.client import get_client


@dataclass(frozen=True)
class ProposalGeneratorSettings:
    source_table: str = "analyzed_tender"
    profiles_table: str = "profiles"
    proposals_table: str = "generated_proposal"
    storage_bucket: str = "proposal-files"

    @classmethod
    def from_env(cls) -> "ProposalGeneratorSettings":
        load_dotenv()
        return cls()


class ProposalGeneratorAgent:
    def __init__(self, settings: ProposalGeneratorSettings | None = None) -> None:
        self.settings = settings or ProposalGeneratorSettings.from_env()
        self.client = get_client()
        self.repository = ProposalRepository(
            table_name=self.settings.proposals_table,
            bucket_name=self.settings.storage_bucket,
            client=self.client,
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            val = value.strip()
            if not val:
                return None
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _tender_from_row(self, row: dict[str, Any]) -> TenderData:
        return TenderData(
            source=str(row.get("source") or "unknown"),
            title=str(row.get("title") or "Untitled tender"),
            country=str(row.get("country") or "unknown"),
            posting_date=self._parse_dt(row.get("posting_date")),
            deadline=self._parse_dt(row.get("deadline")),
            url=row.get("url"),
            description=str(row.get("description") or row.get("decision_reason") or ""),
            external_id=(str(row.get("external_id")) if row.get("external_id") else None),
        )

    def _profile_from_row(self, row: dict[str, Any]) -> CompanyProfileInput:
        return CompanyProfileInput(
            name=str(row.get("name") or "Unnamed profile"),
            description=str(row.get("description") or ""),
            sectors=row.get("sectors") if isinstance(row.get("sectors"), list) else [],
            keywords=row.get("keywords") if isinstance(row.get("keywords"), list) else [],
            locations=row.get("locations") if isinstance(row.get("locations"), list) else [],
            max_budget=row.get("max_budget"),
        )

    def load_input_from_db(self, *, analyzed_tender_id: str, profile_id: str) -> ProposalInput:
        tender_rows = (
            self.client.table(self.settings.source_table)
            .select("*")
            .eq("id", analyzed_tender_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        tender_row = tender_rows[0] if tender_rows else None
        if not tender_row:
            raise ValueError(f"Analyzed tender '{analyzed_tender_id}' not found in {self.settings.source_table}")

        profile_rows = (
            self.client.table(self.settings.profiles_table)
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        profile_row = profile_rows[0] if profile_rows else None
        if not profile_row and profile_id.strip().lower() == "default":
            # Backward-compatible fallback for environments where the default profile
            # row was not initialized in DB yet.
            profile_row = {
                "id": "default",
                "name": "Default Organization",
                "description": "",
                "sectors": [],
                "keywords": [],
                "locations": [],
                "max_budget": None,
            }
        if not profile_row:
            raise ValueError(f"Profile '{profile_id}' not found in {self.settings.profiles_table}")

        return ProposalInput(
            tender=self._tender_from_row(tender_row),
            company_profile=self._profile_from_row(profile_row),
        )

    @staticmethod
    def load_input_from_files(*, tender_file: str, profile_file: str) -> ProposalInput:
        tender_data = json.loads(Path(tender_file).read_text(encoding="utf-8"))
        profile_data = json.loads(Path(profile_file).read_text(encoding="utf-8"))

        return ProposalInput(
            tender=TenderData(
                source=str(tender_data.get("source") or "unknown"),
                title=str(tender_data.get("title") or "Untitled tender"),
                country=str(tender_data.get("country") or "unknown"),
                posting_date=ProposalGeneratorAgent._parse_dt(tender_data.get("posting_date")),
                deadline=ProposalGeneratorAgent._parse_dt(tender_data.get("deadline")),
                url=tender_data.get("url"),
                description=str(tender_data.get("description") or ""),
                external_id=tender_data.get("external_id"),
            ),
            company_profile=CompanyProfileInput(
                name=str(profile_data.get("name") or "Unnamed profile"),
                description=str(profile_data.get("description") or ""),
                sectors=profile_data.get("sectors") if isinstance(profile_data.get("sectors"), list) else [],
                keywords=profile_data.get("keywords") if isinstance(profile_data.get("keywords"), list) else [],
                locations=profile_data.get("locations") if isinstance(profile_data.get("locations"), list) else [],
                max_budget=profile_data.get("max_budget"),
            ),
        )

    def run(self, proposal_input: ProposalInput, save: bool = True, upload_files: bool = True) -> dict[str, Any]:
        ctx = prepare_context(proposal_input)
        outline = build_outline(ctx)
        sections = draft_sections_with_llm(ctx, outline)
        issues = review_compliance(ctx, sections)
        comp_score = compliance_pass_rate(ctx, issues)
        score = score_proposal(ctx, sections, comp_score, issues)

        output = build_proposal_output(
            tender_external_id=proposal_input.tender.external_id,
            profile_name=proposal_input.company_profile.name,
            tender_title=proposal_input.tender.title,
            sections=sections,
            score=score,
            compliance_issues=issues,
            metadata={
                "tender_title": proposal_input.tender.title,
                "risk_flags": ctx.risk_flags,
                "requirements_count": len(ctx.extracted_requirements),
                "compliance_score": comp_score,
            },
        )

        bundle = build_export_bundle(output)
        saved_row: dict[str, Any] | None = None
        storage_paths: dict[str, str] | None = None

        if save:
            saved_row = self.repository.save_proposal(output, bundle["markdown"])
            if upload_files:
                storage_paths = self.repository.upload_artifacts(
                    saved_row,
                    output,
                    bundle["markdown"],
                    docx_bytes=bundle.get("docx_bytes"),
                )

        return {
            "output": output,
            "bundle": bundle,
            "saved_row": saved_row,
            "storage": storage_paths,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Proposal Generator agent end-to-end.")
    parser.add_argument("--analyzed-tender-id", help="ID from analyzed_tender table")
    parser.add_argument("--profile-id", help="Profile ID from profiles table")
    parser.add_argument("--tender-file", help="Path to tender JSON file")
    parser.add_argument("--profile-file", help="Path to profile JSON file")
    parser.add_argument("--no-save", action="store_true", help="Run without saving to Supabase table")
    parser.add_argument("--no-upload", action="store_true", help="Save row but skip storage upload")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    agent = ProposalGeneratorAgent()

    if args.tender_file and args.profile_file:
        proposal_input = agent.load_input_from_files(
            tender_file=args.tender_file,
            profile_file=args.profile_file,
        )
    elif args.analyzed_tender_id and args.profile_id:
        proposal_input = agent.load_input_from_db(
            analyzed_tender_id=args.analyzed_tender_id,
            profile_id=args.profile_id,
        )
    else:
        raise SystemExit(
            "Provide either (--tender-file and --profile-file) or (--analyzed-tender-id and --profile-id)."
        )

    result = agent.run(
        proposal_input,
        save=not args.no_save,
        upload_files=not args.no_upload,
    )

    printable = {
        "decision": result["bundle"]["decision"],
        "total_score": result["bundle"]["total_score"],
        "confidence_score": result["bundle"]["confidence_score"],
        "docx_error": result["bundle"].get("docx_error"),
        "saved_id": (result["saved_row"] or {}).get("id"),
        "storage": result["storage"],
    }
    print(json.dumps(printable, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
