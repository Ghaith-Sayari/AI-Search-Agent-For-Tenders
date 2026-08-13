"""Evaluate Opportunity Analyzer quality on a labeled golden dataset.

Dataset format (JSONL or JSON array):
{
  "unique_key": "sample-1",
  "title": "...",
  "description": "...",
  "country": "Morocco",
  "expected_status": "pursue|review|reject"
}
Legacy labels are accepted and mapped:
- good_fit -> pursue
- needs_review -> review
- not_fit -> reject
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from agents.opportunity_analyzer.analyzers import (
    keyword_analyzer,
    llm_judgment_analyzer,
    location_analyzer,
)
from agents.opportunity_analyzer.models.analysis import Analysis
from agents.opportunity_analyzer.models.opportunity import Opportunity
from agents.opportunity_analyzer.models.profile import Profile
from agents.opportunity_analyzer.scoring.decision import decide
from agents.opportunity_analyzer.scoring.scorer import score_analysis
from agents.opportunity_analyzer.scoring.weights import weight_for


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


def _to_expected_status(value: Any) -> str | None:
    raw = str(value or "").strip().lower()
    mapping = {
        "pursue": "pursue",
        "review": "review",
        "reject": "reject",
        "good_fit": "pursue",
        "needs_review": "review",
        "not_fit": "reject",
    }
    return mapping.get(raw)


def _build_opportunity(sample: dict[str, Any], idx: int) -> Opportunity:
    uid = str(sample.get("unique_key") or f"golden-{idx}")
    return Opportunity(
        id=uid,
        unique_key=uid,
        source=str(sample.get("source") or "golden_dataset"),
        title=str(sample.get("title") or "Untitled sample"),
        country=str(sample.get("country") or "unknown"),
        description=str(sample.get("description") or ""),
        raw_text=sample.get("raw_text") if isinstance(sample.get("raw_text"), str) else None,
        url=sample.get("url"),
        external_id=sample.get("external_id"),
    )


def _build_profile(sample: dict[str, Any]) -> Profile:
    profile_payload = sample.get("profile")
    if not isinstance(profile_payload, dict):
        profile_payload = {}
    return Profile(
        id=str(profile_payload.get("id") or "golden-profile"),
        name=str(profile_payload.get("name") or "Golden Profile"),
        description=str(profile_payload.get("description") or ""),
        sectors=profile_payload.get("sectors") if isinstance(profile_payload.get("sectors"), list) else [],
        keywords=profile_payload.get("keywords") if isinstance(profile_payload.get("keywords"), list) else [],
        locations=profile_payload.get("locations") if isinstance(profile_payload.get("locations"), list) else [],
        min_budget=profile_payload.get("min_budget"),
        max_budget=profile_payload.get("max_budget"),
    )


def _analyze(opportunity: Opportunity, profile: Profile) -> Analysis:
    analysis = Analysis(opportunity_id=opportunity.id, profile_id=profile.id)
    analysis.add_signal(keyword_analyzer.analyze(opportunity, profile, weight_for("keyword")))
    analysis.add_signal(location_analyzer.analyze(opportunity, profile, weight_for("location")))
    analysis.add_signal(llm_judgment_analyzer.analyze(opportunity, profile, weight_for("llm_judgment")))
    score_analysis(analysis)
    decide(analysis)
    return analysis


def _evaluate(rows: list[dict[str, Any]], repeat: int) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    stability_map: dict[str, list[str]] = defaultdict(list)

    for idx, sample in enumerate(rows, start=1):
        expected = _to_expected_status(sample.get("expected_status"))
        opportunity = _build_opportunity(sample, idx)
        profile = _build_profile(sample)
        for _ in range(repeat):
            analysis = _analyze(opportunity, profile)
            predicted = analysis.decision.value
            stability_map[opportunity.id].append(predicted)
            results.append(
                {
                    "unique_key": opportunity.unique_key or opportunity.id,
                    "expected": expected,
                    "predicted": predicted,
                    "score": analysis.total_score,
                    "low_confidence": analysis.low_confidence,
                    "reason": analysis.reasoning,
                }
            )

    with_expected = [r for r in results if r["expected"] is not None]
    correct = sum(1 for r in with_expected if r["expected"] == r["predicted"])
    accuracy = (correct / len(with_expected)) if with_expected else None

    stable = sum(1 for statuses in stability_map.values() if len(set(statuses)) == 1)
    stability = stable / len(stability_map) if stability_map else None

    score_distribution_by_expected: dict[str, dict[str, float | int | None]] = {}
    for label in ("pursue", "review", "reject"):
        subset = [float(r["score"]) for r in with_expected if r.get("expected") == label]
        if not subset:
            score_distribution_by_expected[label] = {"count": 0, "mean": None, "median": None}
            continue
        score_distribution_by_expected[label] = {
            "count": len(subset),
            "mean": round(mean(subset), 4),
            "median": round(median(subset), 4),
        }

    return {
        "samples": len(rows),
        "evaluations": len(results),
        "repeat": repeat,
        "status_distribution": dict(Counter(r["predicted"] for r in results)),
        "accuracy": accuracy,
        "stability": stability,
        "score_distribution_by_expected": score_distribution_by_expected,
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
        print("Create a JSONL file with fields: title, description, expected_status")
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

