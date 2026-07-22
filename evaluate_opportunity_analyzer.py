"""Evaluate Opportunity Analyzer quality on a labeled golden dataset.

Dataset format (JSONL or JSON array):
{
  "unique_key": "sample-1",
  "title": "...",
  "description": "...",
  "country": "Morocco",
  "deadline": "2026-08-15",
  "source": "manual",
  "expected_status": "good_fit|needs_review|not_fit"
}
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from agents.opportunity_analyzer.classifiers.opportunity_classifier import OpportunityClassifier
from agents.opportunity_analyzer.schemas.models import OpportunityStatus, ProductionTenderRecord


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON array dataset must be a list")
        return data
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL line {idx}: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"JSONL line {idx} is not an object")
        rows.append(obj)
    return rows


def _build_record(sample: dict[str, Any], idx: int) -> ProductionTenderRecord:
    now = datetime.now(timezone.utc)
    deadline = sample.get("deadline") or (now.date() + timedelta(days=30)).isoformat()
    return ProductionTenderRecord.model_validate(
        {
            "id": sample.get("id") or str(uuid4()),
            "unique_key": sample.get("unique_key") or f"golden-{idx}",
            "source": sample.get("source") or "golden_dataset",
            "title": sample.get("title") or "Untitled sample",
            "country": sample.get("country"),
            "posting_date": sample.get("posting_date"),
            "deadline": deadline,
            "url": sample.get("url"),
            "description": sample.get("description"),
            "external_id": sample.get("external_id"),
            "staging_tender_id": sample.get("staging_tender_id") or str(uuid4()),
            "gatekeeper_decision_id": sample.get("gatekeeper_decision_id"),
            "created_at": sample.get("created_at") or now.isoformat(),
            "updated_at": sample.get("updated_at") or now.isoformat(),
        }
    )


def _safe_status(value: Any) -> str | None:
    raw = str(value or "").strip().lower()
    valid = {s.value for s in OpportunityStatus}
    return raw if raw in valid else None


def _evaluate(rows: list[dict[str, Any]], repeat: int) -> dict[str, Any]:
    classifier = OpportunityClassifier()
    results: list[dict[str, Any]] = []
    stability_map: dict[str, list[str]] = defaultdict(list)

    for idx, sample in enumerate(rows, start=1):
        expected = _safe_status(sample.get("expected_status"))
        record = _build_record(sample, idx)
        for _ in range(repeat):
            decision = classifier.classify(record)
            predicted = decision.status.value
            stability_map[record.unique_key].append(predicted)
            results.append(
                {
                    "unique_key": record.unique_key,
                    "expected": expected,
                    "predicted": predicted,
                    "score": decision.total_score,
                    "confidence": decision.confidence_score,
                    "reason": decision.decision_reason,
                }
            )

    with_expected = [r for r in results if r["expected"] is not None]
    correct = sum(1 for r in with_expected if r["expected"] == r["predicted"])
    accuracy = (correct / len(with_expected)) if with_expected else None

    tp_good = sum(1 for r in with_expected if r["predicted"] == "good_fit" and r["expected"] == "good_fit")
    fp_good = sum(1 for r in with_expected if r["predicted"] == "good_fit" and r["expected"] != "good_fit")
    fn_good = sum(1 for r in with_expected if r["predicted"] != "good_fit" and r["expected"] == "good_fit")

    precision_good = tp_good / (tp_good + fp_good) if (tp_good + fp_good) else None
    recall_good = tp_good / (tp_good + fn_good) if (tp_good + fn_good) else None

    zero_zero = sum(1 for r in results if float(r["score"]) == 0.0 and float(r["confidence"]) == 0.0)
    unsupported_blocker = sum(1 for r in results if "Unsupported blocker claims were ignored" in (r["reason"] or ""))

    stable = 0
    for statuses in stability_map.values():
        if len(set(statuses)) == 1:
            stable += 1
    stability = stable / len(stability_map) if stability_map else None

    return {
        "samples": len(rows),
        "evaluations": len(results),
        "repeat": repeat,
        "status_distribution": dict(Counter(r["predicted"] for r in results)),
        "accuracy": accuracy,
        "good_fit_precision": precision_good,
        "good_fit_recall": recall_good,
        "good_fit_false_positive_rate": (fp_good / len(with_expected)) if with_expected else None,
        "zero_score_zero_confidence_rate": (zero_zero / len(results)) if results else None,
        "unsupported_blocker_rate": (unsupported_blocker / len(results)) if results else None,
        "stability": stability,
        "details": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Opportunity Analyzer on a labeled dataset.")
    parser.add_argument(
        "--dataset",
        default="tests/opportunity_analyzer/golden_dataset.jsonl",
        help="Path to JSONL/JSON dataset.",
    )
    parser.add_argument("--repeat", type=int, default=1, help="How many repeated runs per sample.")
    parser.add_argument("--output", default="tmp/opportunity_eval_report.json", help="Output JSON report path.")
    args = parser.parse_args()

    if not os.getenv("OPPORTUNITY_ANALYZER_MODEL"):
        print("ERROR: OPPORTUNITY_ANALYZER_MODEL is missing.")
        print("PowerShell example: $env:OPPORTUNITY_ANALYZER_MODEL='llama3.2:3b'")
        return 1

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found: {dataset_path}")
        print("Create a JSONL file with fields: title, description, deadline, expected_status")
        return 1

    rows = _load_dataset(dataset_path)
    if not rows:
        print("ERROR: Dataset is empty.")
        return 1

    report = _evaluate(rows, repeat=max(1, args.repeat))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Evaluation complete.")
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=2, ensure_ascii=False))
    print(f"Saved report: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

