"""Classify one staged tender with an LLM and return a validated decision."""

import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import requests

from pydantic import ValidationError

from agents.gatekeeper.classifiers.settings import GatekeeperSettings
from agents.gatekeeper.schemas import (
    GatekeeperAssessment,
    GatekeeperDecision,
    GatekeeperStatus,
    RawTenderStagingRecord,
)


class GatekeeperClassifier:
    """Loads Gatekeeper policy documents and applies them to one staging row."""

    def __init__(
        self,
        settings: GatekeeperSettings | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or GatekeeperSettings.from_env()
        self.client = client or requests.Session()
        self.system_instructions = self._load_system_instructions()

    def classify(self, record: RawTenderStagingRecord) -> GatekeeperDecision:
        response = self.client.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json={
                "model": self.settings.model,
                "stream": False,
                "format": self._ollama_format_schema(),
                "options": {"temperature": self.settings.temperature},
                "messages": [
                    {"role": "system", "content": self.system_instructions},
                    {
                    "role": "user",
                        "content": self._build_record_message(record),
                    },
                ],
                
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content")
        if not content:
            raise RuntimeError("The Gatekeeper model returned an empty response")

        try:
            raw_payload = json.loads(content)
        except json.JSONDecodeError as e:
            return self._build_failed_decision(record, f"LLM JSON parsing error: {e}. Raw content: {content}")

        if not isinstance(raw_payload, dict):
            return self._build_failed_decision(
                record,
                f"LLM response must be a JSON object. Got: {type(raw_payload).__name__}. Raw content: {content}",
            )

        repaired_payload = self._repair_payload(raw_payload, record)
        try:
            assessment = GatekeeperAssessment.model_validate(repaired_payload)
            return self._build_decision_from_assessment(record, assessment)
        except ValidationError as e:
            return self._build_needs_review_fallback(record, repaired_payload, e)

    def _build_decision_from_assessment(
        self,
        record: RawTenderStagingRecord,
        assessment: GatekeeperAssessment,
    ) -> GatekeeperDecision:
        return GatekeeperDecision(
            staging_tender_id=record.id,
            unique_key=record.unique_key,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
            **assessment.model_dump(),
        )

    def _build_failed_decision(self, record: RawTenderStagingRecord, reason: str) -> GatekeeperDecision:
        return GatekeeperDecision(
            staging_tender_id=record.id,
            unique_key=record.unique_key,
            status=GatekeeperStatus.FAILED,
            confidence_score=0.0,
            decision_reason=reason,
            cleaned_description=None,
            extracted_deadline=None,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
        )

    def _build_needs_review_fallback(
        self,
        record: RawTenderStagingRecord,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> GatekeeperDecision:
        deadline_value = payload.get("extracted_deadline")
        if deadline_value in (None, ""):
            parsed_deadline = self._parse_deadline(record.deadline)
            if parsed_deadline:
                deadline_value = parsed_deadline.isoformat()

        cleaned_description = payload.get("cleaned_description")
        if not isinstance(cleaned_description, str) or not cleaned_description.strip():
            cleaned_description = self._derive_cleaned_description(record, payload)

        reason = payload.get("decision_reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = "Model output failed validation and requires manual review"

        confidence_score = self._coerce_confidence(payload.get("confidence_score"))
        confidence_score = min(confidence_score, 0.84)

        return GatekeeperDecision(
            staging_tender_id=record.id,
            unique_key=record.unique_key,
            status=GatekeeperStatus.NEEDS_REVIEW,
            confidence_score=confidence_score,
            decision_reason=f"Auto-demoted to needs_review after schema validation failure: {error}. Original reason: {reason}",
            cleaned_description=cleaned_description,
            extracted_deadline=deadline_value,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
        )

    def _repair_payload(self, payload: dict[str, Any], record: RawTenderStagingRecord) -> dict[str, Any]:
        repaired = dict(payload)
        repaired.setdefault("cleaned_description", None)
        repaired.setdefault("extracted_deadline", None)

        status = str(repaired.get("status", "")).strip().lower()

        if status in {GatekeeperStatus.APPROVED.value, GatekeeperStatus.NEEDS_REVIEW.value}:
            cleaned_description = repaired.get("cleaned_description")
            if not isinstance(cleaned_description, str) or not cleaned_description.strip():
                repaired["cleaned_description"] = self._derive_cleaned_description(record, repaired)

        if status == GatekeeperStatus.APPROVED.value and repaired.get("extracted_deadline") in (None, ""):
            parsed_deadline = self._parse_deadline(record.deadline)
            if parsed_deadline:
                repaired["extracted_deadline"] = parsed_deadline.isoformat()

        return repaired

    @staticmethod
    def _derive_cleaned_description(record: RawTenderStagingRecord, payload: dict[str, Any]) -> str:
        candidate = payload.get("cleaned_description")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if record.description and record.description.strip():
            return record.description.strip()
        if record.title and record.title.strip():
            return record.title.strip()
        return "Manual review required: cleaned description missing from model output"

    @staticmethod
    def _coerce_confidence(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(score, 0.0), 1.0)

    @classmethod
    def _parse_deadline(cls, value: str | None) -> date | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None

        iso_match = re.match(r"^\d{4}-\d{2}-\d{2}", text)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(0))
            except ValueError:
                pass

        dmY_match = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$", text)
        if dmY_match:
            day, month, year = map(int, dmY_match.groups())
            try:
                return date(year, month, day)
            except ValueError:
                return None

        textual_match = re.match(r"^\s*(\d{1,2})\s+([A-Za-zÀ-ÿ\.]+)\s+(\d{4})\s*$", text)
        if textual_match:
            day_str, month_token, year_str = textual_match.groups()
            month = cls._french_month_to_int(month_token)
            if month is None:
                return None
            try:
                return date(int(year_str), month, int(day_str))
            except ValueError:
                return None

        return None

    @staticmethod
    def _french_month_to_int(token: str) -> int | None:
        normalized = unicodedata.normalize("NFKD", token).encode("ascii", "ignore").decode("ascii")
        normalized = normalized.strip().lower().replace(".", "")
        months = {
            "janvier": 1,
            "janv": 1,
            "fevrier": 2,
            "fevr": 2,
            "fvrier": 2,
            "mars": 3,
            "avril": 4,
            "avr": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "juil": 7,
            "aout": 8,
            "septembre": 9,
            "sept": 9,
            "octobre": 10,
            "oct": 10,
            "novembre": 11,
            "nov": 11,
            "decembre": 12,
            "dec": 12,
        }
        return months.get(normalized)

    @staticmethod
    def _ollama_format_schema() -> dict[str, Any]:
        return GatekeeperAssessment.model_json_schema()

    @staticmethod
    def _build_record_message(record: RawTenderStagingRecord) -> str:
        payload = record.model_dump(mode="json", exclude={"created_at", "updated_at"})
        return (
            "Evaluate this single staged tender. Use only the provided data and "
            "return the required JSON schema.\n\n"
            f"STAGING_RECORD:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def _load_system_instructions() -> str:
        gatekeeper_root = Path(__file__).resolve().parents[1]
        instruction_path = gatekeeper_root / "instructions" / "gatekeeper_instructions.md"
        policy_paths = sorted((gatekeeper_root / "policies").glob("*.md"))

        documents = [instruction_path.read_text(encoding="utf-8")]
        documents.extend(path.read_text(encoding="utf-8") for path in policy_paths)
        return "\n\n---\n\n".join(documents)
