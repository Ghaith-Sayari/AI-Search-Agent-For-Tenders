"""Compatibility pipeline wrapper around OpportunityAnalyzerAgent.

Persistence contract: analyzed_tender only.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from typing import Any, Dict, Optional

if TYPE_CHECKING:
    from agents.opportunity_analyzer.agent import OpportunityAnalyzerAgent


class OpportunityAnalyzerPipeline:
    """Run opportunity analysis and persist outputs into analyzed_tender."""

    def __init__(self, agent: OpportunityAnalyzerAgent | None = None) -> None:
        if agent is not None:
            self.agent = agent
            return

        # Lazy import so this module stays importable in lightweight test
        # environments that do not have runtime DB dependencies installed.
        from agents.opportunity_analyzer.agent import OpportunityAnalyzerAgent as _Agent

        self.agent = _Agent()

    def run(
        self,
        *,
        profile_id: str | None = None,
        limit: Optional[int] = None,
        max_workers: Optional[int] = None,
        continue_on_error: bool = True,
    ) -> Dict[str, Any]:
        resolved_profile_id = (
            (profile_id or "").strip()
            or os.getenv("OPPORTUNITY_ANALYZER_PROFILE_ID", "").strip()
        )
        if not resolved_profile_id:
            raise ValueError(
                "profile_id is required (pass --profile-id or set OPPORTUNITY_ANALYZER_PROFILE_ID)"
            )

        summary = self.agent.run(
            profile_id=resolved_profile_id,
            limit=limit,
            max_workers=max_workers,
            continue_on_error=continue_on_error,
        )

        decision_counts = summary.get("decision_counts", {})
        # Compatibility counters for older callers.
        summary["good_fit_count"] = int(decision_counts.get("pursue", 0))
        summary["needs_review_count"] = int(decision_counts.get("review", 0))
        summary["not_fit_count"] = int(decision_counts.get("reject", 0))
        summary["failed_count"] = int(summary.get("errors", 0))
        return summary
