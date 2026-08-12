from __future__ import annotations

from agents.proposal_generator.models.proposal_output import ProposalOutput


def render_markdown(output: ProposalOutput) -> str:
    """Render ProposalOutput to markdown."""
    return output.to_markdown()
