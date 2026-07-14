"""Classify one staged tender with an LLM and return a validated decision."""

import json
from pathlib import Path
from typing import Any

from agents.gatekeeper.classifiers.settings import GatekeeperSettings
from agents.gatekeeper.schemas import (
    GatekeeperAssessment,
    GatekeeperDecision,
    RawTenderStagingRecord,
)


class GatekeeperClassifier:
    """Loads Gatekeeper policy documents and applies them to one staging row."""

    def __init__(
        self,
        settings: GatekeeperSettings | None = None,
        client: Any | None = None,
        generation_config: Any | None = None,
    ) -> None:
        self.settings = settings or GatekeeperSettings.from_env()
        self.client = client or self._build_gemini_client()
        self.generation_config = (
            generation_config
            if generation_config is not None
            else self._structured_output_config()
        )
        self.system_instructions = self._load_system_instructions()

    def classify(self, record: RawTenderStagingRecord) -> GatekeeperDecision:
        """Return one validated, auditable decision for a staging record."""
        response = self.client.models.generate_content(
            model=self.settings.model,
            contents=(
                f"{self.system_instructions}\n\n---\n\n"
                f"{self._build_record_message(record)}"
            ),
            config=self.generation_config,
        )

        content = response.text
        if not content:
            raise RuntimeError("The Gatekeeper model returned an empty response")

        assessment = GatekeeperAssessment.model_validate_json(content)
        return GatekeeperDecision(
            staging_tender_id=record.id,
            unique_key=record.unique_key,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
            **assessment.model_dump(),
        )

    def _build_gemini_client(self) -> Any:
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError(
                "The 'google-genai' package is required to use the GatekeeperClassifier. "
                "Please install it with 'pip install google-genai'."
            ) from exc
        return genai.Client(api_key=self.settings.gemini_api_key)

    def _structured_output_config(self) -> Any:
        """Build Gemini's Pydantic-backed JSON structured-output configuration."""
        try:
            from google.genai import types
        except ImportError as exc:
            raise ImportError(
                "The 'google-genai' package is required. Install requirements.txt first."
            ) from exc

        return types.GenerateContentConfig(
            temperature=self.settings.temperature,
            response_mime_type="application/json",
            response_schema=GatekeeperAssessment,
        )

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
