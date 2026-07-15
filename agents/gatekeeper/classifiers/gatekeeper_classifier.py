"""Classify one staged tender with an LLM and return a validated decision."""

import json
from pathlib import Path
from typing import Any
import requests

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
        self.client = client or requests.Session()
        self.system_instructions = self._load_system_instructions()

    def classify(self, record: RawTenderStagingRecord) -> GatekeeperDecision:
        response = self.client.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json={
                "model": self.settings.model,
                "stream": False,
                "format": GatekeeperAssessment.model_json_schema(),
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

        assessment = GatekeeperAssessment.model_validate_json(content)
        return GatekeeperDecision(
            staging_tender_id=record.id,
            unique_key=record.unique_key,
            policy_version=self.settings.policy_version,
            agent_version=self.settings.agent_version,
            **assessment.model_dump(),
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