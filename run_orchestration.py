"""CLI helper for LangGraph orchestration.

Examples:
  python run_orchestration.py --print-ascii
  python run_orchestration.py --print-mermaid
  python run_orchestration.py --save-png graph.png
"""

from __future__ import annotations

import argparse
import json
import sys

from orchestration.langgraph.run_service import (
    RunRequest,
    render_graph_ascii,
    render_graph_mermaid,
    run_and_get_summary,
    save_graph_png,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LangGraph orchestration runner/visualizer")
    parser.add_argument(
        "--checkpoint-backend",
        choices=["none", "memory", "sqlite"],
        default="none",
        help="Checkpoint backend used for graph compilation/run.",
    )
    parser.add_argument(
        "--sqlite-checkpoint-path",
        default=None,
        help="SQLite file path when --checkpoint-backend sqlite.",
    )

    parser.add_argument("--print-ascii", action="store_true", help="Print graph as ASCII.")
    parser.add_argument("--print-mermaid", action="store_true", help="Print Mermaid graph text.")
    parser.add_argument("--save-png", default=None, help="Save graph PNG to given path.")

    parser.add_argument("--run", action="store_true", help="Run the orchestration graph.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--mode", default="full")
    parser.add_argument("--profile-id", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--since", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source", action="append", default=None, help="Repeatable source filter.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if not (args.print_ascii or args.print_mermaid or args.save_png or args.run):
        print("Nothing to do. Use --print-ascii, --print-mermaid, --save-png, or --run.", file=sys.stderr)
        return 1

    if args.print_ascii:
        print(render_graph_ascii(checkpoint_backend=args.checkpoint_backend))

    if args.print_mermaid:
        print(render_graph_mermaid(checkpoint_backend=args.checkpoint_backend))

    if args.save_png:
        out = save_graph_png(args.save_png, checkpoint_backend=args.checkpoint_backend)
        print(f"Saved graph PNG: {out}")

    if args.run:
        request = RunRequest(
            mode=args.mode,
            profile_id=args.profile_id,
            limit=args.limit,
            sources=args.source or [],
            since=args.since,
            dry_run=bool(args.dry_run),
            checkpoint_backend=args.checkpoint_backend,
            sqlite_checkpoint_path=args.sqlite_checkpoint_path,
            run_id=args.run_id,
        )
        summary = run_and_get_summary(request)
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

