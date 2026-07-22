"""Tiny runner for Opportunity Analyzer pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pipeline.opportunity_analyzer_pipeline import OpportunityAnalyzerPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Opportunity Analyzer pipeline.")
    parser.add_argument("--limit", type=int, default=5, help="Max number of tenders to process.")
    args = parser.parse_args()

    if not os.getenv("OPPORTUNITY_ANALYZER_MODEL"):
        print("ERROR: OPPORTUNITY_ANALYZER_MODEL is missing.", file=sys.stderr)
        print("Example (PowerShell): $env:OPPORTUNITY_ANALYZER_MODEL='llama3.2:3b'", file=sys.stderr)
        return 1

    summary = OpportunityAnalyzerPipeline().run(limit=args.limit)

    printable = {k: v for k, v in summary.items() if k != "decisions"}
    print(json.dumps(printable, indent=2, default=str, ensure_ascii=False))
    print(f"decisions_count={len(summary.get('decisions', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
