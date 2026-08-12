"""
Small models (llama3.2:3b included) rarely return clean JSON. Typical failure
modes we defend against here:

  1. Wrapped in markdown fences: ```json { ... } ```
  2. Preceded/followed by prose: "Sure! Here's the analysis: { ... } Hope that helps!"
  3. Trailing commas: { "a": 1, "b": 2, }
  4. Single quotes instead of double quotes
  5. Python-style literals: True/False/None instead of true/false/null
  6. Unquoted keys: { name: "value" }

This module tries increasingly aggressive repairs and never raises for
malformed input -- it returns None so callers can decide what to do
(retry, fall back, flag for review).
"""

import json
import re

from agents.opportunity_analyzer.utils.logger import get_logger

logger = get_logger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*([\]}])")
_UNQUOTED_KEY_RE = re.compile(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)")


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    return match.group(1) if match else text


def _extract_json_span(text: str) -> str:
    """Grab the substring between the first '{' and the last matching '}'."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        # try array form
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return text
    return text[start : end + 1]


def _fix_common_issues(text: str) -> str:
    text = _TRAILING_COMMA_RE.sub(r"\1", text)
    text = _UNQUOTED_KEY_RE.sub(r'\1"\2"\3', text)
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)
    return text


def parse_llm_json(raw_text: str) -> dict | list | None:
    """
    Attempt to parse a dict/list out of raw LLM output.
    Returns None if nothing usable could be extracted.
    """
    if not raw_text or not raw_text.strip():
        return None

    candidates = [raw_text]
    stripped = _strip_fences(raw_text)
    if stripped != raw_text:
        candidates.append(stripped)

    span = _extract_json_span(stripped)
    candidates.append(span)
    candidates.append(_fix_common_issues(span))

    for candidate in candidates:
        try:
            result = json.loads(candidate)
            if isinstance(result, (dict, list)):
                return result
        except (json.JSONDecodeError, TypeError):
            continue

    logger.warning("Failed to parse JSON from LLM output: %r", raw_text[:200])
    return None
