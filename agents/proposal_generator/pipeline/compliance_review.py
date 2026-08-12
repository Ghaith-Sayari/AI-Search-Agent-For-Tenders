from __future__ import annotations

from agents.proposal_generator.models.compliance_report import ComplianceIssue
from agents.proposal_generator.models.proposal_section import ProposalSection
from agents.proposal_generator.pipeline.prepare_context import PreparedContext


def _section_text_blob(sections: list[ProposalSection]) -> str:
    return "\n".join((s.title + "\n" + s.content).lower() for s in sections)


def review_compliance(
    ctx: PreparedContext,
    sections: list[ProposalSection],
) -> list[ComplianceIssue]:
    """
    Compare extracted tender requirements against drafted sections.

    Current heuristic (v1):
    - if a requirement phrase is not found in any section text -> high severity
    - if requirement appears only in compliance_matrix section -> medium severity
    """
    issues: list[ComplianceIssue] = []

    if not ctx.extracted_requirements:
        return issues

    all_text = _section_text_blob(sections)
    compliance_text = "\n".join(
        (s.title + "\n" + s.content).lower() for s in sections if s.key == "compliance_matrix"
    )

    for idx, req in enumerate(ctx.extracted_requirements, start=1):
        req_norm = req.lower().strip()
        if not req_norm:
            continue

        req_id = f"req_{idx}"

        if req_norm not in all_text:
            issues.append(
                ComplianceIssue(
                    requirement_id=req_id,
                    message=f"Requirement not covered in drafted proposal: '{req}'.",
                    severity="high",
                    section_key=None,
                )
            )
            continue

        if req_norm in compliance_text:
            appears_outside_matrix = any(
                req_norm in (s.title + "\n" + s.content).lower()
                for s in sections
                if s.key != "compliance_matrix"
            )
            if not appears_outside_matrix:
                issues.append(
                    ComplianceIssue(
                        requirement_id=req_id,
                        message=(
                            f"Requirement '{req}' appears only in compliance mapping; "
                            "add explicit commitment in delivery/technical sections."
                        ),
                        severity="medium",
                        section_key="compliance_matrix",
                    )
                )

    return issues


def compliance_pass_rate(ctx: PreparedContext, issues: list[ComplianceIssue]) -> float:
    """Return naive pass rate in [0,1] from extracted requirements and detected issues."""
    total = len(ctx.extracted_requirements)
    if total == 0:
        return 1.0

    # Count high issues as full miss, medium as half miss.
    penalty = 0.0
    for issue in issues:
        if issue.severity == "high":
            penalty += 1.0
        elif issue.severity == "medium":
            penalty += 0.5
        else:
            penalty += 0.25

    score = max(0.0, 1.0 - (penalty / total))
    return round(score, 4)
