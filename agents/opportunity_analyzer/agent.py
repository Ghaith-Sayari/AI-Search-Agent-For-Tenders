"""Opportunity Analyzer agent runner.

Reads tenders from ``production_tender``, analyzes fit against a selected
company profile, computes score + decision, and persists results to
``analyzed_tender``.
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from agents.opportunity_analyzer.analyzers import (
    keyword_analyzer,
    llm_judgment_analyzer,
    location_analyzer,
)
from agents.opportunity_analyzer.config import config
from agents.opportunity_analyzer.models.analysis import Analysis
from agents.opportunity_analyzer.models.opportunity import Opportunity
from agents.opportunity_analyzer.models.profile import Profile
from agents.opportunity_analyzer.scoring.decision import decide
from agents.opportunity_analyzer.scoring.scorer import score_analysis
from agents.opportunity_analyzer.scoring.weights import weight_for
from agents.opportunity_analyzer.utils.logger import get_logger
from db.client import get_client

logger = get_logger(__name__)


@dataclass(frozen=True)
class OpportunityAnalyzerSettings:
    source_table: str = "production_tender"
    target_table: str = "analyzed_tender"
    profile_table: str = "profiles"
    policy_version: str = "1.0"
    agent_version: str = "1.0"
    max_workers: int = 4

    @classmethod
    def from_env(cls) -> "OpportunityAnalyzerSettings":
        load_dotenv()

        # Keep existing local config compatible with env overrides.
        model = os.getenv("OPPORTUNITY_ANALYZER_MODEL")
        if model:
            config.llm.model = model
        base_url = os.getenv("OPPORTUNITY_ANALYZER_OLLAMA_BASE_URL")
        if base_url:
            config.llm.base_url = base_url.rstrip("/")

        return cls(
            source_table=os.getenv("OPPORTUNITY_ANALYZER_SOURCE_TABLE", "production_tender"),
            target_table=os.getenv("OPPORTUNITY_ANALYZER_TARGET_TABLE", "analyzed_tender"),
            profile_table=os.getenv("OPPORTUNITY_ANALYZER_PROFILE_TABLE", "profiles"),
            policy_version=os.getenv("OPPORTUNITY_ANALYZER_POLICY_VERSION", "1.0"),
            agent_version=os.getenv("OPPORTUNITY_ANALYZER_AGENT_VERSION", "1.0"),
            max_workers=max(1, int(os.getenv("OPPORTUNITY_ANALYZER_MAX_WORKERS", "4"))),
        )


class OpportunityAnalyzerAgent:
    def __init__(self, settings: OpportunityAnalyzerSettings | None = None) -> None:
        self.settings = settings or OpportunityAnalyzerSettings.from_env()
        self.client = get_client()

    def fetch_source_records(self, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        query = self.client.table(self.settings.source_table).select("*").order("created_at", desc=True)
        if limit is not None:
            query = query.range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []

    def get_processed_keys(self, profile_id: str) -> set[tuple[str, str, str]]:
        response = (
            self.client.table(self.settings.target_table)
            .select("unique_key,profile_id,policy_version")
            .eq("profile_id", profile_id)
            .execute()
        )
        rows = response.data or []
        return {
            (str(r.get("unique_key")), str(r.get("profile_id")), str(r.get("policy_version")))
            for r in rows
            if r.get("unique_key") and r.get("profile_id") and r.get("policy_version")
        }

    def load_profile(self, profile_id: str) -> Profile:
        try:
            response = (
                self.client.table(self.settings.profile_table)
                .select("*")
                .eq("id", profile_id)
                .single()
                .execute()
            )
            data = response.data
        except Exception as exc:
            message = str(exc)
            if "PGRST116" in message or "0 rows" in message:
                logger.error(
                    "Profile not found: id='%s' in table '%s'.",
                    profile_id,
                    self.settings.profile_table,
                )
                raise ValueError(
                    f"Profile '{profile_id}' was not found in table '{self.settings.profile_table}'."
                ) from exc
            raise

        if not data:
            logger.error(
                "Profile not found: id='%s' in table '%s'.",
                profile_id,
                self.settings.profile_table,
            )
            raise ValueError(
                f"Profile '{profile_id}' was not found in table '{self.settings.profile_table}'."
            )

        profile = Profile(
            id=str(data.get("id") or profile_id),
            name=str(data.get("name") or "Unnamed profile"),
            description=str(data.get("description") or ""),
            sectors=data.get("sectors") if isinstance(data.get("sectors"), list) else [],
            keywords=data.get("keywords") if isinstance(data.get("keywords"), list) else [],
            locations=data.get("locations") if isinstance(data.get("locations"), list) else [],
            min_budget=data.get("min_budget"),
            max_budget=data.get("max_budget"),
        )
        errors = profile.validate()
        if errors:
            raise ValueError(f"Profile '{profile_id}' is invalid: {'; '.join(errors)}")
        return profile

    @staticmethod
    def _build_opportunity(raw: dict[str, Any], fallback_index: int) -> Opportunity:
        unique_key = str(raw.get("unique_key") or f"prod-{fallback_index}")
        title = str(raw.get("title") or "").strip() or f"Untitled tender {unique_key}"
        country = str(raw.get("country") or "").strip() or "unknown"
        description = str(raw.get("description") or "").strip() or "No description provided."

        return Opportunity(
            id=str(raw.get("id") or unique_key),
            unique_key=unique_key,
            source=raw.get("source"),
            title=title,
            country=country,
            posting_date=None,
            deadline=None,
            url=raw.get("url"),
            external_id=raw.get("external_id"),
            staging_tender_id=(
                str(raw.get("staging_tender_id")) if raw.get("staging_tender_id") else None
            ),
            gatekeeper_decision_id=(
                str(raw.get("gatekeeper_decision_id")) if raw.get("gatekeeper_decision_id") else None
            ),
            description=description,
            raw_text=raw.get("raw_text") if isinstance(raw.get("raw_text"), str) else None,
            metadata={"deadline": raw.get("deadline"), "posting_date": raw.get("posting_date")},
        )

    @staticmethod
    def _signal_payload(analysis: Analysis) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "score": s.score,
                "weight": s.weight,
                "confidence": s.confidence,
                "weighted_score": round(s.weighted_score, 6),
                "details": s.details,
            }
            for s in analysis.signals
        ]

    def _build_target_row(
        self,
        raw: dict[str, Any],
        profile: Profile,
        analysis: Analysis,
    ) -> dict[str, Any]:
        signals = self._signal_payload(analysis)
        llm_signal = next((s for s in analysis.signals if s.name == "llm_judgment"), None)
        keyword_signal = next((s for s in analysis.signals if s.name == "keyword"), None)
        location_signal = next((s for s in analysis.signals if s.name == "location"), None)
        llm_reasoning = ""
        if llm_signal and isinstance(llm_signal.details, dict):
            llm_reasoning = str(llm_signal.details.get("reasoning") or "").strip()

        # Confidence summary: weighted average of signal confidence.
        total_weight = sum(max(0.0, s.weight) for s in analysis.signals) or 1.0
        confidence_score = sum((max(0.0, s.weight) * s.confidence) for s in analysis.signals) / total_weight

        llm_status = "ok"
        llm_error = None
        if llm_signal and isinstance(llm_signal.details, dict):
            llm_status = str(llm_signal.details.get("status") or llm_status)
            llm_error = llm_signal.details.get("error")
            if llm_signal.details.get("stage") == "extraction_validation":
                llm_status = "validation_failed"
                llm_error = "; ".join(llm_signal.details.get("errors") or []) or llm_error

        matched_keywords: list[str] = []
        if keyword_signal and isinstance(keyword_signal.details, dict):
            raw_matched = keyword_signal.details.get("matched_keywords")
            if isinstance(raw_matched, list):
                matched_keywords = [str(x) for x in raw_matched]

        location_match_type = "unknown"
        if location_signal and isinstance(location_signal.details, dict):
            location_match_type = str(
                location_signal.details.get("match_type")
                or location_signal.details.get("reason")
                or location_match_type
            )

        return {
            "production_tender_id": str(raw.get("id")) if raw.get("id") else None,
            "unique_key": str(raw.get("unique_key") or analysis.opportunity_id),
            "profile_id": profile.id,
            "source": raw.get("source"),
            "title": raw.get("title"),
            "country": raw.get("country"),
            "deadline": raw.get("deadline"),
            "url": raw.get("url"),
            "decision": analysis.decision.value,  # pursue/review/reject
            "total_score": round(analysis.total_score * 100.0, 2),  # 0..100 for dashboard sorting
            "total_score_normalized": round(analysis.total_score, 6),  # 0..1 canonical score
            "confidence_score": round(confidence_score, 6),  # 0..1
            "low_confidence": bool(analysis.low_confidence),
            "decision_reason": analysis.reasoning or llm_reasoning or "Scored by Opportunity Analyzer",
            "llm_status": llm_status,
            "llm_error": str(llm_error) if llm_error else None,
            "matched_keywords": matched_keywords,
            "location_match_type": location_match_type,
            "signals": signals,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "policy_version": self.settings.policy_version,
            "agent_version": self.settings.agent_version,
        }

    def _save_target_row(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table(self.settings.target_table)
            .upsert(payload, on_conflict="unique_key,profile_id,policy_version")
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return saved analyzed_tender row")
        return response.data[0]

    def _analyze_single(self, index: int, raw: dict[str, Any], profile: Profile) -> tuple[str, dict[str, Any]]:
        opportunity = self._build_opportunity(raw, fallback_index=index)
        analysis = Analysis(opportunity_id=opportunity.id, profile_id=profile.id)

        analysis.add_signal(keyword_analyzer.analyze(opportunity, profile, weight_for("keyword")))
        analysis.add_signal(location_analyzer.analyze(opportunity, profile, weight_for("location")))
        analysis.add_signal(
            llm_judgment_analyzer.analyze(opportunity, profile, weight_for("llm_judgment"))
        )

        score_analysis(analysis)
        decide(analysis)

        payload = self._build_target_row(raw, profile, analysis)
        self._save_target_row(payload)
        return str(payload["unique_key"]), payload

    def run(
        self,
        profile_id: str,
        limit: int | None = None,
        max_workers: int | None = None,
        continue_on_error: bool = True,
    ) -> dict[str, Any]:
        workers = max(1, max_workers or self.settings.max_workers)
        profile = self.load_profile(profile_id)

        processed_keys = self.get_processed_keys(profile_id)
        source_rows = self.fetch_source_records(limit=limit)

        if not source_rows:
            return {
                "total_fetched": 0,
                "skipped": 0,
                "processed": 0,
                "errors": 0,
                "saved": 0,
                "max_workers": workers,
                "details": [],
            }

        to_process: list[tuple[int, dict[str, Any]]] = []
        skipped_keys: list[str] = []
        for idx, row in enumerate(source_rows, start=1):
            unique_key = str(row.get("unique_key") or f"prod-{idx}")
            key = (unique_key, profile_id, self.settings.policy_version)
            if key in processed_keys:
                skipped_keys.append(unique_key)
                continue
            to_process.append((idx, row))

        details: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        if workers == 1 or len(to_process) <= 1:
            for idx, row in to_process:
                unique_key = str(row.get("unique_key") or f"prod-{idx}")
                try:
                    _, payload = self._analyze_single(idx, row, profile)
                    details.append(payload)
                except Exception as exc:
                    if not continue_on_error:
                        raise
                    errors.append(
                        {
                            "index": idx,
                            "unique_key": unique_key,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        }
                    )
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._analyze_single, idx, row, profile): (idx, row)
                    for idx, row in to_process
                }
                for future in as_completed(futures):
                    idx, row = futures[future]
                    unique_key = str(row.get("unique_key") or f"prod-{idx}")
                    try:
                        _, payload = future.result()
                        details.append(payload)
                    except Exception as exc:
                        if not continue_on_error:
                            raise
                        errors.append(
                            {
                                "index": idx,
                                "unique_key": unique_key,
                                "error": str(exc),
                                "error_type": type(exc).__name__,
                            }
                        )

        details.sort(key=lambda d: str(d.get("unique_key")))
        errors.sort(key=lambda d: d["index"])

        decision_counts: dict[str, int] = {"pursue": 0, "review": 0, "reject": 0}
        for d in details:
            decision = str(d.get("decision") or "review")
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        return {
            "total_fetched": len(source_rows),
            "skipped": len(skipped_keys),
            "skipped_keys": skipped_keys,
            "processed": len(details),
            "saved": len(details),
            "errors": len(errors),
            "error_details": errors,
            "decision_counts": decision_counts,
            "profile_id": profile_id,
            "policy_version": self.settings.policy_version,
            "target_table": self.settings.target_table,
            "max_workers": workers,
            "details": details,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Opportunity Analyzer against production_tender.")
    parser.add_argument("--profile-id", required=True, help="Profile ID from the profiles table.")
    parser.add_argument("--limit", type=int, default=10, help="Max number of tenders to process.")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="How many tenders to analyze concurrently (overrides env OPPORTUNITY_ANALYZER_MAX_WORKERS).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first analysis error.",
    )
    args = parser.parse_args()

    try:
        agent = OpportunityAnalyzerAgent()
        summary = agent.run(
            profile_id=args.profile_id,
            limit=max(1, args.limit) if args.limit is not None else None,
            max_workers=args.max_workers,
            continue_on_error=not args.fail_fast,
        )
    except Exception as exc:
        logger.error("Opportunity Analyzer failed: %s", exc)
        return 1

    printable = {k: v for k, v in summary.items() if k != "details"}
    print(json.dumps(printable, indent=2, ensure_ascii=False, default=str))
    print(f"saved_rows={summary.get('saved', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
