"""Service layer for proposal engine endpoints."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from agents.proposal_generator.agent import ProposalGeneratorAgent
from agents.proposal_generator.models.compliance_report import ComplianceIssue
from agents.proposal_generator.models.proposal_output import ProposalOutput
from agents.proposal_generator.models.proposal_section import ProposalSection
from agents.proposal_generator.renderers.docx_renderer import render_proposal_docx_bytes
from api.mappers.proposal_mapper import db_row_to_proposal
from api.repositories.proposal_repository import ProposalApiRepository
from api.schemas.proposals import (
    CreateProposalPayload,
    ExportProposalPayload,
    ExportProposalResponse,
    Proposal,
    ProposalPatch,
    ProposalQualityMetrics,
    ProposalSectionDTO,
    RegenerateSectionPayload,
)


class ProposalGenerationError(RuntimeError):
    """Raised when proposal generation fails after backend state has been updated."""


class ProposalService:
    def __init__(self, repository: ProposalApiRepository | None = None) -> None:
        self.repository = repository or ProposalApiRepository()

    def list_proposals(self) -> list[Proposal]:
        return [db_row_to_proposal(r) for r in self.repository.list()]

    def get_proposal(self, proposal_id: str) -> Proposal | None:
        row = self.repository.get(proposal_id)
        if not row:
            return None
        return db_row_to_proposal(row)

    def create_proposal(self, payload: CreateProposalPayload) -> Proposal:
        opp = self.repository.get_analyzed_opportunity(payload.opportunityId)
        if not opp:
            raise ValueError(f"Opportunity '{payload.opportunityId}' not found in analyzed_tender")
        profile = self.repository.get_profile(payload.companyProfileId)
        row = self.repository.create_draft(
            opportunity_row=opp,
            profile_row=profile,
            payload=payload.model_dump(),
        )
        return db_row_to_proposal(row)

    def generate_proposal(self, proposal_id: str) -> Proposal | None:
        row = self.repository.get(proposal_id)
        if not row:
            return None

        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        analyzed_id = str(meta.get("analyzed_tender_id") or meta.get("opportunity_id") or "")
        profile_id = str(meta.get("company_profile_id") or "default")
        if not analyzed_id:
            patched = self.repository.update(
                proposal_id,
                {
                    "metadata": {
                        "status": "FAILED",
                        "generation_error": "Missing opportunity reference for this draft.",
                    },
                    "executive_summary": "Proposal generation failed.",
                },
            )
            _ = db_row_to_proposal(patched) if patched else None
            raise ProposalGenerationError("Missing opportunity reference for this proposal draft.")

        # Backward compatibility: old drafts may store an opportunity id that is not the
        # analyzed_tender primary key. Resolve it to the actual analyzed_tender row id.
        analyzed_row = self.repository.get_analyzed_opportunity(analyzed_id)
        if not analyzed_row:
            _ = self.repository.update(
                proposal_id,
                {
                    "metadata": {
                        "status": "FAILED",
                        "generation_error": f"Analyzed tender '{analyzed_id}' not found.",
                    },
                    "executive_summary": "Proposal generation failed.",
                },
            )
            raise ProposalGenerationError(f"Analyzed tender '{analyzed_id}' not found.")

        resolved_analyzed_id = str(analyzed_row.get("id") or analyzed_id)

        # Set generating status
        self.repository.update(
            proposal_id,
            {
                "metadata": {
                    "status": "GENERATING",
                    "generation_error": None,
                    "analyzed_tender_id": resolved_analyzed_id,
                },
            },
        )

        try:
            agent = ProposalGeneratorAgent()
            proposal_input = agent.load_input_from_db(
                analyzed_tender_id=resolved_analyzed_id,
                profile_id=profile_id,
            )
            result = agent.run(proposal_input, save=False, upload_files=False)
            output = result["output"]
            bundle = result["bundle"]

            sections = [
                {
                    "id": s.key,
                    "key": s.key,
                    "title": s.title,
                    "content": s.content,
                    "status": "GENERATED",
                    "lastUpdated": datetime.now(timezone.utc).isoformat(),
                }
                for s in output.sections
            ]

            patch = {
                "decision": output.decision,
                "total_score": float(output.total_score),
                "confidence_score": float(output.confidence_score),
                "executive_summary": str(output.executive_summary or ""),
                "sections": sections,
                "markdown": bundle.get("markdown", ""),
                "metadata": {
                    "status": "READY_FOR_REVIEW",
                    "risk_flags": output.metadata.get("risk_flags", []) if isinstance(output.metadata, dict) else [],
                    "requirements_count": output.metadata.get("requirements_count", 0)
                    if isinstance(output.metadata, dict)
                    else 0,
                    "generation_error": None,
                },
            }
            updated = self.repository.update(proposal_id, patch)
            return db_row_to_proposal(updated) if updated else None
        except Exception as exc:  # noqa: BLE001
            _ = self.repository.update(
                proposal_id,
                {
                    "metadata": {"status": "FAILED", "generation_error": str(exc)},
                    "executive_summary": "Proposal generation failed.",
                },
            )
            raise ProposalGenerationError(f"Proposal generation failed: {exc}") from exc

    def patch_proposal(self, proposal_id: str, patch: ProposalPatch) -> Proposal | None:
        patch_payload = patch.model_dump(exclude_none=True)
        if "config" in patch_payload and isinstance(patch_payload["config"], dict):
            # keep nested model shape stable
            patch_payload["config"] = {k: v for k, v in patch_payload["config"].items() if v is not None}
        if "sections" in patch_payload and isinstance(patch_payload["sections"], list):
            patch_payload["sections"] = [
                {k: v for k, v in s.items() if v is not None}
                for s in patch_payload["sections"]
                if isinstance(s, dict)
            ]
        updated = self.repository.update(proposal_id, patch_payload)
        return db_row_to_proposal(updated) if updated else None

    def regenerate_section(
        self,
        proposal_id: str,
        section_id: str,
        payload: RegenerateSectionPayload,
    ) -> ProposalSectionDTO | None:
        row = self.repository.get(proposal_id)
        if not row:
            return None
        sections = row.get("sections") if isinstance(row.get("sections"), list) else []
        updated_sections: list[dict[str, Any]] = []
        target: ProposalSectionDTO | None = None
        for s in sections:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("id") or s.get("key") or "")
            if sid == section_id:
                new_content = self.repository.build_placeholder_section(
                    payload.action,
                    section_id,
                    str(s.get("content") or ""),
                )
                ns = dict(s)
                ns["content"] = new_content
                ns["status"] = "GENERATED"
                ns["lastUpdated"] = datetime.now(timezone.utc).isoformat()
                updated_sections.append(ns)
                target = ProposalSectionDTO(
                    id=section_id,
                    title=str(ns.get("title") or section_id),
                    content=new_content,
                    status="GENERATED",
                    lastUpdated=ns["lastUpdated"],
                )
            else:
                updated_sections.append(s)

        if target is None:
            return None
        _ = self.repository.update(proposal_id, {"sections": updated_sections})
        return target

    def get_quality(self, proposal_id: str) -> ProposalQualityMetrics | None:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        return proposal.qualityMetrics

    def export_proposal(self, proposal_id: str, payload: ExportProposalPayload) -> ExportProposalResponse | None:
        row = self.repository.get(proposal_id)
        if not row:
            return None
        proposal_output = self._proposal_output_from_row(row)
        markdown = str(row.get("markdown") or proposal_output.to_markdown())

        if payload.format == "markdown":
            file_obj = self.repository.upload_export(
                proposal_id=proposal_id,
                fmt="markdown",
                content=markdown.encode("utf-8"),
            )
        elif payload.format == "docx":
            tender_title = str(
                (row.get("metadata") if isinstance(row.get("metadata"), dict) else {}).get("tender_title")
                or "Tender Proposal"
            )
            docx_bytes = render_proposal_docx_bytes(proposal_output, tender_title=tender_title)
            file_obj = self.repository.upload_export(
                proposal_id=proposal_id,
                fmt="docx",
                content=docx_bytes,
            )
        else:  # pdf
            pdf_bytes = self._render_pdf_bytes(proposal_output)
            file_obj = self.repository.upload_export(
                proposal_id=proposal_id,
                fmt="pdf",
                content=pdf_bytes,
            )

        _ = self.repository.update(proposal_id, {"metadata": {"status": "EXPORTED"}})
        return ExportProposalResponse(**file_obj)

    @staticmethod
    def _proposal_output_from_row(row: dict[str, Any]) -> ProposalOutput:
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        sections_raw = row.get("sections") if isinstance(row.get("sections"), list) else []
        issues_raw = row.get("compliance_issues") if isinstance(row.get("compliance_issues"), list) else []

        sections: list[ProposalSection] = []
        for idx, s in enumerate(sections_raw):
            if not isinstance(s, dict):
                continue
            sid = str(s.get("key") or s.get("id") or f"section-{idx+1}")
            sections.append(
                ProposalSection(
                    key=sid,
                    title=str(s.get("title") or sid),
                    content=str(s.get("content") or ""),
                    order=int(s.get("order") or (idx + 1)),
                    requirement_ids=s.get("requirement_ids") if isinstance(s.get("requirement_ids"), list) else [],
                )
            )

        issues: list[ComplianceIssue] = []
        for i in issues_raw:
            if not isinstance(i, dict):
                continue
            issues.append(
                ComplianceIssue(
                    requirement_id=str(i.get("requirement_id") or ""),
                    message=str(i.get("message") or ""),
                    severity=str(i.get("severity") or "medium"),
                    section_key=str(i.get("section_key")) if i.get("section_key") else None,
                )
            )

        generated_at_raw = row.get("generated_at")
        generated_at = datetime.now(timezone.utc)
        if isinstance(generated_at_raw, str) and generated_at_raw.strip():
            try:
                generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
            except ValueError:
                generated_at = datetime.now(timezone.utc)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)

        output = ProposalOutput(
            tender_external_id=(str(row.get("tender_external_id")) if row.get("tender_external_id") else None),
            profile_name=str(row.get("profile_name") or "Unknown profile"),
            sections=sections,
            executive_summary=str(row.get("executive_summary") or ""),
            total_score=float(row.get("total_score") or 0.0),
            confidence_score=float(row.get("confidence_score") or 0.0),
            decision=str(row.get("decision") or "review"),
            compliance_issues=issues,
            generated_at=generated_at,
            metadata=meta,
        )
        # Keep safe bounds
        output = replace(
            output,
            total_score=min(1.0, max(0.0, output.total_score)),
            confidence_score=min(1.0, max(0.0, output.confidence_score)),
        )
        return output

    @staticmethod
    def _render_pdf_bytes(output: ProposalOutput) -> bytes:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            ) from exc

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        x_margin = 2 * cm
        y = height - 2 * cm
        max_width_chars = 105

        def write_line(line: str, font: str = "Helvetica", size: int = 10) -> None:
            nonlocal y
            if y < 2 * cm:
                c.showPage()
                y = height - 2 * cm
            c.setFont(font, size)
            c.drawString(x_margin, y, line[:1800])
            y -= 14

        def wrap_text(text: str, width_chars: int = max_width_chars) -> list[str]:
            words = text.split()
            if not words:
                return [""]
            lines: list[str] = []
            current = words[0]
            for w in words[1:]:
                candidate = f"{current} {w}"
                if len(candidate) <= width_chars:
                    current = candidate
                else:
                    lines.append(current)
                    current = w
            lines.append(current)
            return lines

        write_line("Tender Proposal", font="Helvetica-Bold", size=16)
        write_line(f"Company: {output.profile_name}", font="Helvetica", size=11)
        write_line(f"Tender External ID: {output.tender_external_id or 'N/A'}")
        write_line(f"Decision: {output.decision.upper()}  |  Score: {output.total_score:.2f}  |  Confidence: {output.confidence_score:.2f}")
        write_line("")
        write_line("Executive Summary", font="Helvetica-Bold", size=12)
        for line in wrap_text(output.executive_summary or ""):
            write_line(line)
        write_line("")

        for section in sorted(output.sections, key=lambda s: s.order):
            write_line(section.title, font="Helvetica-Bold", size=12)
            for paragraph in (section.content or "").splitlines():
                if not paragraph.strip():
                    write_line("")
                    continue
                for line in wrap_text(paragraph.strip()):
                    write_line(line)
            write_line("")

        if output.compliance_issues:
            write_line("Compliance Issues", font="Helvetica-Bold", size=12)
            for issue in output.compliance_issues:
                text = f"- [{issue.severity.upper()}] {issue.requirement_id}: {issue.message}"
                for line in wrap_text(text):
                    write_line(line)

        c.save()
        return buffer.getvalue()
