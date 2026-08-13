"""Tiny runner for Opportunity Analyzer pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pipeline.opportunity_analyzer_pipeline import OpportunityAnalyzerPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Opportunity Analyzer pipeline.")
    parser.add_argument(
        "--profile-id",
        default=os.getenv("OPPORTUNITY_ANALYZER_PROFILE_ID"),
        help="Profile ID from profiles table. Defaults to OPPORTUNITY_ANALYZER_PROFILE_ID.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Max number of tenders to process.")
    parser.add_argument("--max-workers", type=int, default=None, help="Parallel worker count.")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first analysis error.",
    )
    args = parser.parse_args()

    if not os.getenv("OPPORTUNITY_ANALYZER_MODEL"):
        print("ERROR: OPPORTUNITY_ANALYZER_MODEL is missing.", file=sys.stderr)
        print("Example (PowerShell): $env:OPPORTUNITY_ANALYZER_MODEL='llama3.2:3b'", file=sys.stderr)
        return 1

    if not args.profile_id:
        print(
            "ERROR: profile id is missing. Pass --profile-id or set OPPORTUNITY_ANALYZER_PROFILE_ID.",
            file=sys.stderr,
        )
        return 1

    summary = OpportunityAnalyzerPipeline().run(
        profile_id=args.profile_id,
        limit=args.limit,
        max_workers=args.max_workers,
        continue_on_error=not args.fail_fast,
    )

    printable = {k: v for k, v in summary.items() if k != "details"}
    print(json.dumps(printable, indent=2, default=str, ensure_ascii=False))
    print(f"saved_rows={summary.get('saved', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
