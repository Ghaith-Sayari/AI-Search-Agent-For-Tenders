"""
Pure keyword overlap analyzer. No LLM, no embeddings -- this is one of the
'boring but reliable' signals that keeps the overall score sane even if
the LLM-derived signal has a bad day.
"""

import re

from models.opportunity import Opportunity
from models.profile import Profile
from models.analysis import SignalScore

_SYNONYM_PHRASES: dict[str, set[str]] = {
    "managed services": {"managed support", "24/7 managed support", "24x7 managed support"},
    "api security": {"secure api gateways", "api gateway security", "secure api gateway"},
    "cloud transformation": {"cloud modernization", "cloud infrastructure modernization"},
    "devops": {"devops automation", "ci cd", "ci/cd"},
}
_NEGATION_TOKENS = {"no", "not", "without", "exclud", "except"}


def _normalize_word(word: str) -> str:
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    # very light stemming to keep behavior deterministic/simple
    for suffix in ("ing", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suffix):
            w = w[: -len(suffix)]
            break
    return w


def _tokenize(text: str) -> set[str]:
    return {_normalize_word(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if _normalize_word(t)}


def _normalize_phrase(text: str) -> str:
    return " ".join(_normalize_word(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if _normalize_word(t))


def _ngram_set(tokens: list[str], n: int) -> set[str]:
    if n <= 0 or len(tokens) < n:
        return set()
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _expand_keyword_variants(keyword: str) -> set[str]:
    normalized = _normalize_phrase(keyword)
    variants = {normalized} if normalized else set()

    # canonical + reverse mapping (all normalized)
    for canonical, alternatives in _SYNONYM_PHRASES.items():
        canonical_norm = _normalize_phrase(canonical)
        normalized_alts = {_normalize_phrase(v) for v in alternatives}
        if normalized == canonical_norm or normalized in normalized_alts:
            variants.add(canonical_norm)
            variants |= normalized_alts

    return {v for v in variants if v}


def _token_match(a: str, b: str) -> bool:
    """
    Token-level soft match:
    - exact normalized token match
    - shared prefix (>=5 chars) for close variants: secure/security, modernize/modernization
    """
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]:
        return True
    return False


def _find_contiguous_matches(variant_tokens: list[str], opportunity_tokens: list[str]) -> list[tuple[int, int]]:
    """Find contiguous token spans where variant tokens match (with soft token matching)."""
    if not variant_tokens or not opportunity_tokens or len(variant_tokens) > len(opportunity_tokens):
        return []

    spans: list[tuple[int, int]] = []
    n = len(variant_tokens)
    for i in range(len(opportunity_tokens) - n + 1):
        if all(_token_match(variant_tokens[j], opportunity_tokens[i + j]) for j in range(n)):
            spans.append((i, i + n - 1))
    return spans


def _is_negated_span(opportunity_tokens: list[str], start: int, end: int) -> bool:
    """
    Negation guard:
    if exclusion terms appear close to the matched span, treat it as a non-match.
    """
    left = max(0, start - 8)
    right = min(len(opportunity_tokens), end + 9)
    window = opportunity_tokens[left:right]

    # Generic nearby negation words
    if any(t in _NEGATION_TOKENS for t in window):
        return True

    # Common procurement exclusion phrasing
    window_text = " ".join(window)
    if "not part of" in window_text or "not required" in window_text:
        return True

    return False


def _has_local_token_overlap(
    variant_tokens: list[str], opportunity_tokens: list[str], min_ratio: float = 0.67
) -> bool:
    """
    Checks semantic phrase overlap within a local window (not globally across the full text).
    This avoids false positives where tokens appear far apart in unrelated context.
    """
    if not variant_tokens or not opportunity_tokens:
        return False

    window_size = min(len(opportunity_tokens), max(len(variant_tokens) + 3, 4))
    for i in range(len(opportunity_tokens) - window_size + 1):
        window = opportunity_tokens[i : i + window_size]
        matched = 0
        for vt in variant_tokens:
            if any(_token_match(vt, wt) for wt in window):
                matched += 1
        if (matched / len(variant_tokens)) >= min_ratio:
            # approximate span for negation guard
            if not _is_negated_span(opportunity_tokens, i, i + window_size - 1):
                return True
    return False


def _keyword_matches(keyword: str, opportunity_text: str, opp_tokens: set[str]) -> bool:
    keyword = keyword.strip()
    if not keyword:
        return False

    keyword_variants = _expand_keyword_variants(keyword)
    if not keyword_variants:
        return False

    opportunity_tokens = [_normalize_word(t) for t in re.findall(r"[a-z0-9]+", opportunity_text.lower())]
    opportunity_tokens = [t for t in opportunity_tokens if t]
    opportunity_text_norm = " ".join(opportunity_tokens)
    opp_bigrams = _ngram_set(opportunity_tokens, 2)
    opp_trigrams = _ngram_set(opportunity_tokens, 3)

    for variant in keyword_variants:
        variant_tokens = [t for t in variant.split() if t]
        if not variant_tokens:
            continue

        # Fast exact phrase check on normalized text + negation guard on span
        if variant in opportunity_text_norm:
            spans = _find_contiguous_matches(variant_tokens, opportunity_tokens)
            for start, end in spans:
                if not _is_negated_span(opportunity_tokens, start, end):
                    return True

        # N-gram exact checks for phrase variants
        if (len(variant_tokens) == 2 and variant in opp_bigrams) or (
            len(variant_tokens) >= 3 and variant in opp_trigrams
        ):
            spans = _find_contiguous_matches(variant_tokens, opportunity_tokens)
            for start, end in spans:
                if not _is_negated_span(opportunity_tokens, start, end):
                    return True

        # Single-token keyword: any soft token match in opportunity tokens
        if len(variant_tokens) == 1:
            vt = variant_tokens[0]
            for idx, ot in enumerate(opportunity_tokens):
                if _token_match(vt, ot) and not _is_negated_span(opportunity_tokens, idx, idx):
                    return True
            continue

        # Multi-token keyword: accept if most tokens are present semantically
        if _has_local_token_overlap(variant_tokens, opportunity_tokens, min_ratio=0.67):
            return True

    return False


def analyze(opportunity: Opportunity, profile: Profile, weight: float) -> SignalScore:
    if not profile.keywords:
        # No keywords configured -- neutral score, flagged low confidence
        # so the scorer knows not to lean on this signal.
        return SignalScore(
            name="keyword",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={"reason": "no keywords configured on profile"},
        )

    opportunity_text = opportunity.full_text()
    opp_tokens = _tokenize(opportunity_text)
    matched = [kw for kw in profile.keywords if _keyword_matches(kw, opportunity_text, opp_tokens)]

    score = len(matched) / len(profile.keywords)
    score = min(score, 1.0)

    return SignalScore(
        name="keyword",
        score=score,
        weight=weight,
        confidence=1.0,
        details={"matched_keywords": matched, "total_keywords": len(profile.keywords)},
    )
