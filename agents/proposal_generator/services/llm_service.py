from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import requests

from agents.proposal_generator.config import config
from agents.proposal_generator.pipeline.prepare_context import PreparedContext

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_SECTION_PROMPTS_DIR = _PROMPTS_DIR / "sections"
_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ProposalLLMError(RuntimeError):
    pass


def _read_prompt(name: str) -> str:
    path = _PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")

def _read_section_prompt(name: str) -> str:
    path = _SECTION_PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def _safe_format(template: str, **kwargs: Any) -> str:
    return _PLACEHOLDER_RE.sub(lambda m: str(kwargs.get(m.group(1), m.group(0))), template)


def _ctx_to_kwargs(ctx: PreparedContext) -> dict[str, Any]:
    return {
        "tender_title": ctx.tender_title,
        "source": ctx.source,
        "country": ctx.country,
        "deadline": ctx.deadline.isoformat() if ctx.deadline else "N/A",
        "description": ctx.description,
        "requirements": "; ".join(ctx.extracted_requirements) if ctx.extracted_requirements else "N/A",
        "risk_flags": ", ".join(ctx.risk_flags) if ctx.risk_flags else "none",
        "company_name": ctx.company_name,
        "company_description": ctx.company_description,
        "sectors": ", ".join(ctx.sectors) if ctx.sectors else "N/A",
        "keywords": ", ".join(ctx.keywords) if ctx.keywords else "N/A",
        "locations": ", ".join(ctx.locations) if ctx.locations else "N/A",
        "max_budget": ctx.max_budget if ctx.max_budget is not None else "N/A",
    }

def _template_for_section_key(section_key: str) -> str:
    mapping = {
        "understanding_of_needs": "understanding_of_needs.md",
        "technical_approach": "technical_approach.md",
        "delivery_plan": "delivery_plan.md",
        "team_and_capabilities": "team_and_capabilities.md",
        "compliance_matrix": "compliance_matrix.md",
        "risk_mitigation": "risk_mitigation.md",
    }
    return mapping.get(section_key, "generic.md")


def _call_ollama(prompt: str) -> str:
    endpoint = f"{config.llm.base_url}/api/generate"
    system_prompt = _read_prompt("system.md")

    last_err: Exception | None = None
    for attempt in range(1, config.llm.max_retries + 1):
        try:
            response = requests.post(
                endpoint,
                json={
                    "model": config.llm.model,
                    "system": system_prompt,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.llm.temperature,
                        "num_predict": config.llm.max_tokens,
                    },
                },
                timeout=config.llm.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            text = str(data.get("response") or "").strip()
            if not text:
                raise ProposalLLMError("LLM returned empty response text")
            return text
        except (requests.RequestException, ValueError, ProposalLLMError) as exc:
            last_err = exc
            if attempt < config.llm.max_retries:
                time.sleep(config.llm.retry_backoff_seconds * attempt)

    raise ProposalLLMError(
        f"LLM call failed after {config.llm.max_retries} retries "
        f"(model='{config.llm.model}', endpoint='{endpoint}'): {last_err}"
    )


def generate_section_text(
    section_key: str,
    section_title: str,
    section_guidance: str,
    ctx: PreparedContext,
) -> str:
    """Generate one proposal section body from context and outline guidance."""
    template = _read_section_prompt(_template_for_section_key(section_key))
    tone = _read_prompt("tone_style.md")
    prompt = _safe_format(
        template,
        section_key=section_key,
        section_title=section_title,
        section_guidance=section_guidance,
        **_ctx_to_kwargs(ctx),
    )
    return _call_ollama(f"{prompt}\n\n{tone}")
