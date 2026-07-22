"""LLM-first semantic scorer for opportunity fit assessment."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests
import yaml
from pydantic import ValidationError

from agents.opportunity_analyzer.classifiers.settings import OpportunityAnalyzerSettings
from agents.opportunity_analyzer.schemas.models import (
    BudgetSource,
    OpportunityAssessment,
    OpportunityStatus,
    ProductionTenderRecord,
    RiskLevel,
)


class LLMSemanticScorer:
    """Ask the LLM to produce a structured OpportunityAssessment."""

    def __init__(
        self,
        settings: OpportunityAnalyzerSettings | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or OpportunityAnalyzerSettings.from_env()
        self.client = client or requests.Session()
        self.system_instructions = self._load_system_instructions()

    def score(self, record: ProductionTenderRecord) -> OpportunityAssessment:
        """Generate one structured assessment for a production tender."""
        budget_context = self._build_budget_context(record)
        try:
            response = self._invoke_model(record, budget_context)
            response.raise_for_status()
        except Exception as exc:
            return self._build_failed_assessment(f"LLM request failed: {exc}")

        content = response.json().get("message", {}).get("content")
        if not content:
            return self._build_failed_assessment("The analyzer model returned an empty response")

        try:
            payload = self._parse_json_payload(content)
        except Exception as exc:
            return self._build_failed_assessment(f"LLM JSON parsing error: {exc}")

        payload = self._attach_budget_metadata(payload, budget_context)

        try:
            return OpportunityAssessment.model_validate(payload)
        except ValidationError as exc:
            return self._build_needs_review_fallback(payload, exc)

    def _invoke_model(self, record: ProductionTenderRecord, budget_context: dict[str, Any]) -> Any:
        return self.client.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json={
                "model": self.settings.model,
                "stream": False,
                "format": OpportunityAssessment.model_json_schema(),
                "options": {"temperature": self.settings.temperature},
                "messages": [
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": self._build_record_message(record, budget_context)},
                ],
            },
            timeout=45,
        )

    @staticmethod
    def _build_record_message(record: ProductionTenderRecord, budget_context: dict[str, Any]) -> str:
        payload = record.model_dump(mode="json")
        return (
            "Evaluate this single production tender against the supplied company profile "
            "and policies. Return only JSON matching the required schema.\n\n"
            f"PRODUCTION_TENDER:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
            f"BUDGET_CONTEXT:\n{json.dumps(budget_context, ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def _attach_budget_metadata(payload: dict[str, Any], budget_context: dict[str, Any]) -> dict[str, Any]:
        updated = dict(payload)
        method = str(budget_context.get("method", "")).strip().lower()
        existing_budget_source = LLMSemanticScorer._coerce_budget_source(payload.get("budget_source"))
        if method == "extracted_from_text":
            updated["budget_source"] = existing_budget_source or BudgetSource.EXTRACTED.value
            updated.setdefault("budget_eur", budget_context.get("extracted_budget_eur"))
            updated.setdefault("budget_range_min_eur", budget_context.get("extracted_budget_eur"))
            updated.setdefault("budget_range_max_eur", budget_context.get("extracted_budget_eur"))
            updated.setdefault(
                "budget_estimation_rationale",
                f"Extracted explicit amount from text: {budget_context.get('budget_evidence', 'n/a')}",
            )
        elif method == "estimated_from_scope":
            updated["budget_source"] = existing_budget_source or BudgetSource.ESTIMATED.value
            updated.setdefault("budget_eur", budget_context.get("estimated_budget_mid_eur"))
            updated.setdefault("budget_range_min_eur", budget_context.get("estimated_budget_min_eur"))
            updated.setdefault("budget_range_max_eur", budget_context.get("estimated_budget_max_eur"))
            updated.setdefault("budget_estimation_rationale", budget_context.get("estimation_rationale"))
        else:
            updated["budget_source"] = existing_budget_source or BudgetSource.UNKNOWN.value
            updated.setdefault("budget_estimation_rationale", "No budget evidence or estimation available")
        return updated

    @staticmethod
    def _build_budget_context(record: ProductionTenderRecord) -> dict[str, Any]:
        text = " ".join([(record.title or ""), (record.description or "")]).strip()
        extracted = LLMSemanticScorer._extract_budget_to_eur(text)
        if extracted is not None:
            return {
                "method": "extracted_from_text",
                "currency_rates_used": {
                    "EUR": 1.0,
                    "USD": 0.92,
                    "MAD": 0.092,
                    "TND": 0.30,
                    "GBP": 1.16,
                },
                **extracted,
            }

        low, high, rationale = LLMSemanticScorer._estimate_budget_range_eur(text)
        return {
            "method": "estimated_from_scope",
            "estimated_budget_min_eur": low,
            "estimated_budget_max_eur": high,
            "estimated_budget_mid_eur": round((low + high) / 2, 2),
            "estimation_rationale": rationale,
        }

    @staticmethod
    def _extract_budget_to_eur(text: str) -> dict[str, Any] | None:
        if not text:
            return None
        rates = {
            "EUR": 1.0,
            "\u20ac": 1.0,
            "USD": 0.92,
            "$": 0.92,
            "MAD": 0.092,
            "DH": 0.092,
            "TND": 0.30,
            "GBP": 1.16,
        }
        pattern_after = re.compile(
            r"(?P<amount>\d[\d\s.,]{1,18})\s*(?P<currency>EUR|USD|MAD|DH|TND|GBP|\u20ac|\$)(?!\w)",
            flags=re.IGNORECASE,
        )
        pattern_before = re.compile(
            r"(?<!\w)(?P<currency>EUR|USD|MAD|DH|TND|GBP|\u20ac|\$)\s*(?P<amount>\d[\d\s.,]{1,18})",
            flags=re.IGNORECASE,
        )

        candidates = []
        for pattern in (pattern_after, pattern_before):
            for match in pattern.finditer(text):
                currency_raw = match.group("currency").upper()
                amount_raw = match.group("amount")
                amount = LLMSemanticScorer._parse_decimal_number(amount_raw)
                if amount is None or amount <= 0:
                    continue
                rate = rates.get(currency_raw)
                if rate is None:
                    continue
                candidates.append(
                    {
                        "original_amount": amount,
                        "original_currency": currency_raw,
                        "amount_eur": round(amount * rate, 2),
                        "evidence_snippet": match.group(0),
                    }
                )

        if not candidates:
            return None

        best = max(candidates, key=lambda x: x["amount_eur"])
        return {
            "original_amount": best["original_amount"],
            "original_currency": best["original_currency"],
            "extracted_budget_eur": best["amount_eur"],
            "budget_evidence": best["evidence_snippet"],
        }

    @staticmethod
    def _estimate_budget_range_eur(text: str) -> tuple[float, float, str]:
        t = (text or "").lower()
        has_it_cluster = LLMSemanticScorer._matches_it_cluster(t)
        rules = [
            (
                ["civil works", "public lighting", "road rehabilitation", "infrastructure", "green corridor", "construction"],
                (350000, 2500000),
                "civil/infrastructure scope",
            ),
            (["architectural", "engineering study", "monitoring"], (40000, 300000), "architectural/engineering study scope"),
            (["bus", "buses", "vehicle", "acquisition"], (120000, 900000), "equipment/vehicle acquisition scope"),
            (["consulting", "consultancy", "training"], (15000, 150000), "consulting/training scope"),
        ]
        for keywords, band, rationale in rules:
            if any(k in t for k in keywords):
                return float(band[0]), float(band[1]), rationale
        if has_it_cluster:
            return 40000.0, 700000.0, "digital/IT scope (multi-signal)"
        return 50000.0, 400000.0, "default generic tender band"

    @staticmethod
    def _matches_it_cluster(text: str) -> bool:
        strong_phrases = [
            "software development",
            "information system",
            "cyber security",
            "cloud migration",
            "data platform",
            "ai solution",
            "machine learning",
        ]
        if any(phrase in text for phrase in strong_phrases):
            return True
        token_patterns = {
            "software": r"\bsoftware\b",
            "it": r"\bit\b",
            "cloud": r"\bcloud\b",
            "cyber": r"\bcyber(?:security)?\b",
            "data": r"\bdata\b",
            "api": r"\bapi\b",
            "digital": r"\bdigital\b",
            "platform": r"\bplatform\b",
        }
        hits = sum(1 for pattern in token_patterns.values() if re.search(pattern, text))
        return hits >= 2

    @staticmethod
    def _parse_decimal_number(raw: str) -> float | None:
        value = re.sub(r"\s+", "", raw)
        if not value:
            return None
        if "," in value and "." in value:
            if value.rfind(",") > value.rfind("."):
                value = value.replace(".", "").replace(",", ".")
            else:
                value = value.replace(",", "")
        elif "," in value:
            if value.count(",") == 1 and len(value.split(",")[-1]) <= 2:
                value = value.replace(",", ".")
            else:
                value = value.replace(",", "")
        try:
            return float(value)
        except ValueError:
            return None

    def _load_system_instructions(self) -> str:
        analyzer_root = Path(__file__).resolve().parents[1]
        instruction_path = analyzer_root / "instructions" / "analyzer_instructions.md"
        policy_paths = sorted((analyzer_root / "policies").glob("*.md"))

        documents: list[str] = []
        if instruction_path.exists():
            documents.append(instruction_path.read_text(encoding="utf-8"))

        for path in policy_paths:
            documents.append(path.read_text(encoding="utf-8"))

        documents.append(self._render_scoring_context())
        documents.append(self._render_company_profile_context())

        return "\n\n---\n\n".join(documents)

    def _render_scoring_context(self) -> str:
        scoring_cfg = self.settings.scoring
        if scoring_cfg is None:
            path = self.settings.scoring_config_path
            return f"SCORING_CONFIG_PATH: {path}"

        return (
            "SCORING_CONFIG_SUMMARY:\n"
            f"- version: {scoring_cfg.version}\n"
            f"- range: {scoring_cfg.score_range.min}..{scoring_cfg.score_range.max}\n"
            "- weights:\n"
            f"  - domain_relevance: {scoring_cfg.weights.domain_relevance}\n"
            f"  - geography_fit: {scoring_cfg.weights.geography_fit}\n"
            f"  - budget_fit: {scoring_cfg.weights.budget_fit}\n"
            f"  - eligibility_fit: {scoring_cfg.weights.eligibility_fit}\n"
            f"  - strategic_fit: {scoring_cfg.weights.strategic_fit}\n"
            "- thresholds:\n"
            f"  - good_fit_min: {scoring_cfg.thresholds.good_fit_min}\n"
            f"  - needs_review_min: {scoring_cfg.thresholds.needs_review_min}\n"
            f"  - not_fit_max: {scoring_cfg.thresholds.not_fit_max}\n"
            "- confidence:\n"
            f"  - default: {scoring_cfg.confidence.default}\n"
            f"  - min_for_auto_decision: {scoring_cfg.confidence.min_for_auto_decision}\n"
            "- risk:\n"
            f"  - default_level: {scoring_cfg.risk.default_level}\n"
            f"  - high_risk_keywords: {scoring_cfg.risk.high_risk_keywords}\n"
            f"  - blocker_keywords: {scoring_cfg.risk.blocker_keywords}"
        )

    def _render_company_profile_context(self) -> str:
        profile_path = self.settings.company_profile_path
        if not profile_path.exists():
            return f"COMPANY_PROFILE_PATH_NOT_FOUND: {profile_path}"

        try:
            raw = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        except Exception:
            return f"COMPANY_PROFILE_PATH_UNREADABLE: {profile_path}"

        return "COMPANY_PROFILE:\n" + json.dumps(raw or {}, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_json_payload(content: str) -> dict[str, Any]:
        cleaned = content.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            candidate = LLMSemanticScorer._extract_first_json_object(cleaned)
            parsed = json.loads(candidate)

        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got: {type(parsed).__name__}")
        return parsed

    @staticmethod
    def _extract_first_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON object found in LLM response")
        return text[start : end + 1]

    @staticmethod
    def _coerce_score(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(numeric, 0.0), 100.0)

    @staticmethod
    def _coerce_confidence(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(numeric, 0.0), 1.0)

    @staticmethod
    def _coerce_string_list(value: Any, fallback: list[str] | None = None) -> list[str]:
        if not isinstance(value, list):
            return fallback or []
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned

    @staticmethod
    def _coerce_budget_source(value: Any) -> str | None:
        raw = str(value or "").strip().lower()
        for allowed in BudgetSource:
            if raw == allowed.value:
                return raw
        return None

    @staticmethod
    def _coerce_risk_level(value: Any) -> RiskLevel:
        raw = str(value or "").strip().lower()
        for allowed in RiskLevel:
            if raw == allowed.value:
                return allowed
        return RiskLevel.MEDIUM

    def _build_needs_review_fallback(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> OpportunityAssessment:
        breakdown_input = payload.get("score_breakdown")
        breakdown: dict[str, float] = {}
        if isinstance(breakdown_input, dict):
            for key, value in breakdown_input.items():
                key_text = str(key).strip()
                if not key_text:
                    continue
                breakdown[key_text] = self._coerce_score(value)

        reason = payload.get("decision_reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = "Model output failed validation and requires manual review"

        return OpportunityAssessment(
            status=OpportunityStatus.NEEDS_REVIEW,
            total_score=self._coerce_score(payload.get("total_score")),
            confidence_score=min(self._coerce_confidence(payload.get("confidence_score")), 0.64),
            decision_reason=f"Auto-demoted to needs_review after schema validation failure: {error}. "
            f"Original reason: {reason}",
            risk_level=self._coerce_risk_level(payload.get("risk_level")),
            score_breakdown=breakdown,
            blockers=self._coerce_string_list(payload.get("blockers")),
            blocker_evidence={},
            strengths=self._coerce_string_list(payload.get("strengths")),
            gaps=self._coerce_string_list(payload.get("gaps"), fallback=["Validation fallback triggered"]),
            budget_source=self._coerce_budget_source(payload.get("budget_source")) or BudgetSource.UNKNOWN.value,
            budget_eur=payload.get("budget_eur"),
            budget_range_min_eur=payload.get("budget_range_min_eur"),
            budget_range_max_eur=payload.get("budget_range_max_eur"),
            budget_estimation_rationale=payload.get("budget_estimation_rationale"),
        )

    @staticmethod
    def _build_failed_assessment(reason: str) -> OpportunityAssessment:
        return OpportunityAssessment(
            status=OpportunityStatus.FAILED,
            total_score=0.0,
            confidence_score=0.0,
            decision_reason=reason,
            risk_level=RiskLevel.HIGH,
            score_breakdown={},
            blockers=[],
            blocker_evidence={},
            strengths=[],
            gaps=["Automatic scoring unavailable"],
            budget_source=BudgetSource.UNKNOWN.value,
            budget_estimation_rationale="Scoring failed before budget estimation could be applied",
        )
