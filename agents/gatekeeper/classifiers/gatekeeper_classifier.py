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
    ) -> None:
        self.settings = settings or GatekeeperSettings.from_env()
        self.client = client or self._build_openai_client()
        self.system_instructions = self._load_system_instructions()

    def classify(self, record: RawTenderStagingRecord) -> GatekeeperDecision:
        """Return one validated, auditable decision for a staging record."""
        completion = self.client.chat.completions.create(
            model=self.settings.azure_openai_deployment_name,
            temperature=self.settings.temperature,
            messages=[
                {"role": "system", "content": self.system_instructions},
                {
                    "role": "user",
                    "content": self._build_record_message(record),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "gatekeeper_assessment",
                    "strict": True,
                    "schema": GatekeeperAssessment.model_json_schema(),
                },
            },
        )

        content = completion.choices[0].message.content
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

    def _build_openai_client(self) -> Any:
        try:
            if self.settings.use_azure:
                from openai import AzureOpenAI
                return AzureOpenAI(
                    api_key=self.settings.openai_api_key,
                    azure_endpoint=self.settings.azure_endpoint,
                    api_version=self.settings.api_version,
                )
            else:
                from openai import OpenAI
                return OpenAI(api_key=self.settings.openai_api_key)
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required to use the GatekeeperClassifier. "
                "Please install it with 'pip install openai'."
            ) from exc

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
