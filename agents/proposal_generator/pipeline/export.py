from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agents.proposal_generator.models.compliance_report import ComplianceIssue
from agents.proposal_generator.models.proposal_output import ProposalOutput
from agents.proposal_generator.models.proposal_section import ProposalSection
from agents.proposal_generator.pipeline.score_proposal import ProposalScore
from agents.proposal_generator.renderers.docx_renderer import render_proposal_docx_bytes
from agents.proposal_generator.renderers.markdown_renderer import render_markdown


def _build_executive_summary(
    company_name: str,
    tender_title: str,
    sections: list[ProposalSection],
    score: ProposalScore,
    compliance_issues: list[ComplianceIssue],
) -> str:
    issue_count = len(compliance_issues)
    section_count = len(sections)

    return (
        f"{company_name} submits this proposal for '{tender_title}' with {section_count} structured sections. "
        f"Current automated assessment indicates a {score.decision.upper()} recommendation "
        f"(score: {score.total_score:.2f}, confidence: {score.confidence_score:.2f}). "
        f"Detected compliance issues: {issue_count}."
    )


def build_proposal_output(
    *,
    tender_external_id: Optional[str],
    profile_name: str,
    tender_title: str,
    sections: list[ProposalSection],
    score: ProposalScore,
    compliance_issues: list[ComplianceIssue],
    metadata: Optional[dict] = None,
    executive_summary: Optional[str] = None,
) -> ProposalOutput:
    """Compose the final ProposalOutput from pipeline artifacts."""
    summary = executive_summary or _build_executive_summary(
        company_name=profile_name,
        tender_title=tender_title,
        sections=sections,
        score=score,
        compliance_issues=compliance_issues,
    )

    payload = ProposalOutput(
        tender_external_id=tender_external_id,
        profile_name=profile_name,
        sections=sections,
        executive_summary=summary,
        total_score=score.total_score,
        confidence_score=score.confidence_score,
        decision=score.decision,
        compliance_issues=compliance_issues,
        generated_at=datetime.now(timezone.utc),
        metadata={
            "scoring_reasoning": score.reasoning,
            **(metadata or {}),
        },
    )

    errors = payload.validate()
    if errors:
        raise ValueError(f"Invalid ProposalOutput: {'; '.join(errors)}")

    return payload


def build_export_bundle(output: ProposalOutput) -> dict:
    """Return a ready-to-save bundle containing JSON-safe fields + markdown/docx."""
    markdown = render_markdown(output)
    tender_title = str(output.metadata.get("tender_title") or "Tender Proposal")
    docx_bytes = None
    docx_error = None
    try:
        docx_bytes = render_proposal_docx_bytes(output, tender_title=tender_title)
    except Exception as exc:
        docx_error = str(exc)

    return {
        "tender_external_id": output.tender_external_id,
        "profile_name": output.profile_name,
        "decision": output.decision,
        "total_score": output.total_score,
        "confidence_score": output.confidence_score,
        "generated_at": output.generated_at.isoformat(),
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
        "markdown": markdown,
        "docx_bytes": docx_bytes,
        "docx_error": docx_error,
    }
