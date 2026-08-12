from __future__ import annotations

from dataclasses import dataclass

from agents.proposal_generator.pipeline.prepare_context import PreparedContext


@dataclass
class OutlineItem:
    key: str
    title: str
    guidance: str
    order: int


def build_outline(ctx: PreparedContext) -> list[OutlineItem]:
    """Build a first-pass proposal outline from prepared context."""
    items: list[OutlineItem] = [
        OutlineItem(
            key="understanding_of_needs",
            title="Understanding of Needs",
            guidance="Summarize the buyer objectives, scope, and expected outcomes from the tender.",
            order=1,
        ),
        OutlineItem(
            key="technical_approach",
            title="Technical Approach",
            guidance="Describe how the solution will be delivered with methods, tools, and quality controls.",
            order=2,
        ),
        OutlineItem(
            key="delivery_plan",
            title="Delivery Plan and Timeline",
            guidance="Provide phases, milestones, and delivery cadence aligned with tender deadlines.",
            order=3,
        ),
        OutlineItem(
            key="team_and_capabilities",
            title="Team and Capabilities",
            guidance="Highlight relevant company strengths, sectors, keywords, and execution capability.",
            order=4,
        ),
        OutlineItem(
            key="compliance_matrix",
            title="Compliance and Requirements Coverage",
            guidance="Map stated requirements to concrete responses and evidence of compliance.",
            order=5,
        ),
    ]

    # Optional risk section only when there are flagged risks.
    if ctx.risk_flags:
        items.append(
            OutlineItem(
                key="risk_mitigation",
                title="Risk Mitigation",
                guidance="Address timeline, location, or delivery risks with mitigation actions.",
                order=6,
            )
        )

    return sorted(items, key=lambda x: x.order)


def outline_as_prompt_payload(outline: list[OutlineItem]) -> list[dict[str, str | int]]:
    """Convert outline items to LLM-friendly payload."""
    return [
        {
            "key": item.key,
            "title": item.title,
            "guidance": item.guidance,
            "order": item.order,
        }
        for item in outline
    ]
