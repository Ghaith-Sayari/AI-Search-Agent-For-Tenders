from __future__ import annotations

from typing import Callable, Optional

from agents.proposal_generator.models.proposal_section import ProposalSection
from agents.proposal_generator.pipeline.build_outline import OutlineItem
from agents.proposal_generator.pipeline.prepare_context import PreparedContext

# Signature expected from an LLM writer function.
# Input: section key + title + guidance + prepared context
# Output: generated section text
SectionWriter = Callable[[str, str, str, PreparedContext], str]


def _fallback_section_content(item: OutlineItem, ctx: PreparedContext) -> str:
    """Deterministic section draft used when no LLM writer is provided."""
    if item.key == "understanding_of_needs":
        return (
            f"The tender '{ctx.tender_title}' published by {ctx.source} in {ctx.country} "
            "requires a partner able to deliver reliable outcomes aligned with the stated scope. "
            "Our proposal focuses on measurable delivery quality, transparent coordination, "
            "and strict adherence to submission requirements."
        )

    if item.key == "technical_approach":
        keyword_line = ", ".join(ctx.keywords) if ctx.keywords else "best-practice methods"
        return (
            "We propose a structured implementation approach combining discovery, execution, and validation. "
            f"The delivery model leverages {keyword_line} and quality checkpoints to ensure compliance, "
            "traceability, and performance across all required deliverables."
        )

    if item.key == "delivery_plan":
        deadline_txt = ctx.deadline.isoformat() if ctx.deadline else "the contractual deadline"
        return (
            "The project will be delivered in phases: initiation, build, verification, and handover. "
            f"Milestones are planned backward from {deadline_txt} to reduce schedule risk and keep stakeholders aligned."
        )

    if item.key == "team_and_capabilities":
        sectors = ", ".join(ctx.sectors) if ctx.sectors else "relevant sectors"
        return (
            f"{ctx.company_name} brings proven capabilities in {sectors}. "
            "Our cross-functional team combines domain expertise, delivery discipline, "
            "and continuous communication to ensure timely and high-quality execution."
        )

    if item.key == "compliance_matrix":
        if ctx.extracted_requirements:
            reqs = "\n".join([f"- {r}" for r in ctx.extracted_requirements[:10]])
            return (
                "The following key requirements are explicitly covered in this proposal:\n"
                f"{reqs}\n"
                "Each requirement is mapped to a concrete response and delivery evidence."
            )
        return (
            "A detailed compliance matrix will map every tender requirement to explicit "
            "commitments, methods, and evidence artifacts."
        )

    if item.key == "risk_mitigation":
        flags = ", ".join(ctx.risk_flags) if ctx.risk_flags else "delivery risks"
        return (
            f"Identified risk areas include: {flags}. "
            "Mitigation actions include tighter milestone governance, proactive communication, "
            "and contingency allocation for critical activities."
        )

    return item.guidance


def draft_sections(
    ctx: PreparedContext,
    outline: list[OutlineItem],
    writer: Optional[SectionWriter] = None,
) -> list[ProposalSection]:
    """
    Draft proposal sections from outline + context.

    If `writer` is provided, it is used for each section (typically LLM-based).
    Otherwise a deterministic fallback draft is generated.
    """
    sections: list[ProposalSection] = []

    for item in sorted(outline, key=lambda x: x.order):
        if writer:
            content = writer(item.key, item.title, item.guidance, ctx).strip()
        else:
            content = _fallback_section_content(item, ctx).strip()

        # Link requirement IDs naively for compliance-related section.
        requirement_ids: list[str] = []
        if item.key == "compliance_matrix" and ctx.extracted_requirements:
            requirement_ids = [f"req_{idx+1}" for idx, _ in enumerate(ctx.extracted_requirements)]

        sections.append(
            ProposalSection(
                key=item.key,
                title=item.title,
                content=content,
                order=item.order,
                requirement_ids=requirement_ids,
            )
        )

    return sections


def draft_sections_with_llm(ctx: PreparedContext, outline: list[OutlineItem]) -> list[ProposalSection]:
    """Convenience wrapper that uses the configured LLM service."""
    from agents.proposal_generator.services.llm_service import generate_section_text

    return draft_sections(ctx=ctx, outline=outline, writer=generate_section_text)
