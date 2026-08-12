from __future__ import annotations

from dataclasses import dataclass

from agents.proposal_generator.models.compliance_report import ComplianceIssue
from agents.proposal_generator.models.proposal_section import ProposalSection
from agents.proposal_generator.pipeline.prepare_context import PreparedContext


@dataclass(frozen=True)
class ProposalScore:
    total_score: float  # 0..1
    confidence_score: float  # 0..1
    decision: str  # pursue | review | reject
    reasoning: str


def _sections_completeness_score(sections: list[ProposalSection]) -> float:
    if not sections:
        return 0.0

    non_empty = sum(1 for s in sections if s.content and s.content.strip())
    ratio = non_empty / len(sections)

    long_sections = sum(1 for s in sections if len((s.content or "").strip()) >= 220)
    depth_bonus = 0.15 * (long_sections / len(sections))

    return min(1.0, round(ratio + depth_bonus, 4))


def _risk_penalty(ctx: PreparedContext) -> float:
    if not ctx.risk_flags:
        return 0.0

    weights = {
        "deadline_passed": 0.50,
        "short_timeline": 0.20,
        "location_mismatch": 0.15,
    }
    penalty = sum(weights.get(flag, 0.10) for flag in ctx.risk_flags)
    return min(0.7, round(penalty, 4))


def _compliance_penalty(issues: list[ComplianceIssue]) -> float:
    if not issues:
        return 0.0

    penalty = 0.0
    for issue in issues:
        if issue.severity == "high":
            penalty += 0.20
        elif issue.severity == "medium":
            penalty += 0.10
        else:
            penalty += 0.05

    return min(0.8, round(penalty, 4))


def score_proposal(
    ctx: PreparedContext,
    sections: list[ProposalSection],
    compliance_score: float,
    compliance_issues: list[ComplianceIssue],
) -> ProposalScore:
    """
    Compute proposal quality score + confidence + decision.

    Weighted formula (v1):
    - compliance_score: 55%
    - content completeness: 30%
    - risk adjusted reserve: 15% (inverse of risk penalty)
    Then apply direct penalties for compliance issues and risks.
    """
    compliance_score = max(0.0, min(1.0, compliance_score))
    completeness = _sections_completeness_score(sections)
    risk_pen = _risk_penalty(ctx)
    comp_pen = _compliance_penalty(compliance_issues)

    risk_component = max(0.0, 1.0 - risk_pen)

    base = (0.55 * compliance_score) + (0.30 * completeness) + (0.15 * risk_component)
    total = max(0.0, min(1.0, base - comp_pen))

    # Confidence driven by structure stability + amount of explicit issues.
    confidence = max(
        0.0,
        min(
            1.0,
            (0.6 * completeness) + (0.25 * compliance_score) + (0.15 * (1.0 - min(1.0, len(compliance_issues) / 8))),
        ),
    )

    if total >= 0.75 and confidence >= 0.65:
        decision = "pursue"
    elif total >= 0.45:
        decision = "review"
    else:
        decision = "reject"

    reasoning = (
        f"Score={total:.2f} (compliance={compliance_score:.2f}, completeness={completeness:.2f}, "
        f"risk_penalty={risk_pen:.2f}, compliance_penalty={comp_pen:.2f}); "
        f"confidence={confidence:.2f}; decision={decision}."
    )

    return ProposalScore(
        total_score=round(total, 4),
        confidence_score=round(confidence, 4),
        decision=decision,
        reasoning=reasoning,
    )
