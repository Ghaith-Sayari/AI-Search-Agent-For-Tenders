"""
Wraps calls to the local llama3.2:3b model via ollama's /api/generate.

Design principle: every method here returns an LLMResponse, never raises
for a bad/unparseable model output. Callers decide what "bad output"
means for their use case (retry, fall back to deterministic score, flag
for review). Network/connection errors DO raise (via retry's re-raise)
since those are infrastructure problems, not model-quality problems.
"""

import json
from pathlib import Path
import re
from typing import Any, Union

import requests

from config import config
from models.llm_response import LLMResponse, LLMResponseStatus
from utils.json_parser import parse_llm_json
from utils.logger import get_logger
from utils.retry import retry

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

SECTOR_TAXONOMY = [
    "IT Services",
    "Construction",
    "Healthcare",
    "Education",
    "Energy",
    "Transport",
    "Agriculture",
    "Finance",
    "Public Administration",
    "Other",
]

_SECTOR_KEYWORDS = {
    "IT Services": ["cloud", "devops", "cyber", "api", "software", "saas", "it", "digital", "data center"],
    "Construction": ["road", "bridge", "building", "construction", "civil works", "infrastructure"],
    "Healthcare": ["hospital", "clinic", "medical", "health", "pharma", "patient"],
    "Education": ["school", "university", "education", "learning", "curriculum", "training center"],
    "Energy": ["energy", "power", "solar", "wind", "grid", "electricity", "battery"],
    "Transport": ["transport", "rail", "airport", "port", "logistics", "fleet", "mobility"],
    "Agriculture": ["agriculture", "farming", "irrigation", "crop", "livestock", "agri"],
    "Finance": ["bank", "insurance", "fintech", "payment", "treasury", "financial"],
    "Public Administration": ["ministry", "government", "municipal", "public sector", "state", "authority"],
}

_SECTOR_ALIASES = {
    "it services": "IT Services",
    "information technology": "IT Services",
    "it": "IT Services",
    "construction": "Construction",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "education": "Education",
    "energy": "Energy",
    "transport": "Transport",
    "agriculture": "Agriculture",
    "finance": "Finance",
    "public administration": "Public Administration",
    "public sector": "Public Administration",
    "government": "Public Administration",
    "other": "Other",
}


_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _get_system_prompt() -> str:
    """Load system prompt with explicit UTF-8 encoding."""
    return (_PROMPTS_DIR / "system.md").read_text(encoding="utf-8")


def _load_prompt(filename: str, **kwargs: Any) -> str:
    """
    Load and format a prompt template using safe placeholder replacement.

    Only placeholders of the form {identifier} are substituted; all other
    braces (such as JSON schema braces) are left untouched.
    """
    template_text = (_PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return _PLACEHOLDER_RE.sub(
        lambda m: str(kwargs.get(m.group(1), m.group(0))),
        template_text,
    )


@retry(
    max_attempts=config.llm.max_retries,
    backoff_seconds=config.llm.retry_backoff_seconds,
    exceptions=(requests.RequestException,),
)
def _call_ollama(prompt: str, temperature: float) -> str:
    response = requests.post(
        f"{config.llm.base_url}/api/generate",
        json={
            "model": config.llm.model,
            "system": _get_system_prompt(),
            "prompt": prompt,
            "format": "json",  # Enforces JSON mode natively in Ollama
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": config.llm.max_tokens,
            },
        },
        timeout=config.llm.timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def _normalize_sector(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    if cleaned in SECTOR_TAXONOMY:
        return cleaned

    lowered = cleaned.lower()
    if lowered in _SECTOR_ALIASES:
        return _SECTOR_ALIASES[lowered]

    for canonical in SECTOR_TAXONOMY:
        if canonical.lower() == lowered:
            return canonical
    return None


def _infer_sector_from_keywords(text: str) -> str | None:
    lowered = (text or "").lower()
    if not lowered.strip():
        return None

    best_sector: str | None = None
    best_hits = 0
    for sector, keywords in _SECTOR_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits > best_hits:
            best_hits = hits
            best_sector = sector
    return best_sector if best_hits > 0 else None


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, parsed))


def _postprocess_extraction(data: dict[str, Any], opportunity_text: str) -> dict[str, Any]:
    """
    Enforces sector inference policy:
    - normalize model sector to fixed taxonomy
    - infer sector from keywords when model gives null/invalid sector
    - provide sector_confidence
    - if confidence is very low, map to "Other"
    """
    result = dict(data)
    model_sector = _normalize_sector(result.get("sector"))
    sector_confidence = _coerce_confidence(result.get("sector_confidence"))

    if model_sector is None:
        inferred = _infer_sector_from_keywords(opportunity_text)
        if inferred is not None:
            model_sector = inferred
            if sector_confidence is None:
                sector_confidence = 0.55
        else:
            if sector_confidence is None:
                sector_confidence = 0.0

    if model_sector is not None and sector_confidence is None:
        sector_confidence = 0.70

    if model_sector is not None and sector_confidence is not None and sector_confidence < 0.45:
        model_sector = "Other"

    result["sector"] = model_sector
    result["sector_confidence"] = sector_confidence if sector_confidence is not None else 0.0
    return result


def _generate_structured(prompt_name: str, prompt_text: str, temperature: float) -> LLMResponse:
    try:
        raw_text = _call_ollama(prompt_text, temperature)
    except requests.RequestException as e:
        logger.error("LLM call failed after retries for %s: %s", prompt_name, e)
        return LLMResponse(
            status=LLMResponseStatus.ERROR,
            prompt_name=prompt_name,
            error=str(e),
        )

    if not raw_text.strip():
        return LLMResponse(
            status=LLMResponseStatus.EMPTY,
            prompt_name=prompt_name,
            raw_text=raw_text,
        )

    parsed = parse_llm_json(raw_text)
    if parsed is None or not isinstance(parsed, dict):
        return LLMResponse(
            status=LLMResponseStatus.PARSE_FAILED,
            prompt_name=prompt_name,
            raw_text=raw_text,
            error="Failed to parse model output as a JSON object",
        )

    return LLMResponse(
        status=LLMResponseStatus.OK,
        data=parsed,
        raw_text=raw_text,
        prompt_name=prompt_name,
    )


def extract(opportunity_text: str) -> LLMResponse:
    """Extract structured fields from raw opportunity text."""
    prompt = _load_prompt("output_schema.md", opportunity_text=opportunity_text)
    response = _generate_structured("extraction", prompt, config.llm.extraction_temperature)
    if response.status == LLMResponseStatus.OK and isinstance(response.data, dict):
        response.data = _postprocess_extraction(response.data, opportunity_text)
    return response


def analyze_fit(profile_text: str, extracted_json: Union[str, dict]) -> LLMResponse:
    """Judge fit between a profile and previously-extracted opportunity details."""
    if isinstance(extracted_json, dict):
        extracted_json_str = json.dumps(extracted_json, indent=2)
    else:
        extracted_json_str = str(extracted_json)

    prompt = _load_prompt(
        "analyze.md",
        profile_text=profile_text,
        extracted_json=extracted_json_str,
    )
    return _generate_structured("analysis", prompt, config.llm.analysis_temperature)
