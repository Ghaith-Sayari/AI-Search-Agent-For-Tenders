"""Embedding-based semantic similarity signal (lightweight, non-generative)."""

from __future__ import annotations

import math
from typing import Any

from agents.opportunity_analyzer.models.analysis import SignalScore
from agents.opportunity_analyzer.models.opportunity import Opportunity
from agents.opportunity_analyzer.models.profile import Profile
from agents.opportunity_analyzer.services import llm_service


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def analyze(opportunity: Opportunity, profile: Profile, weight: float) -> SignalScore:
    profile_text = profile.full_text().strip()
    opportunity_text = opportunity.full_text().strip()

    if not profile_text or not opportunity_text:
        return SignalScore(
            name="semantic",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={"reason": "missing profile/opportunity text for embedding"},
        )

    # Keep embedding payload compact enough for fast local inference.
    profile_text = profile_text[:6000]
    opportunity_text = opportunity_text[:6000]

    try:
        profile_vec = llm_service.embed(profile_text)
        opportunity_vec = llm_service.embed(opportunity_text)
        cosine = _cosine_similarity(profile_vec, opportunity_vec)  # -1..1
        score = _clamp01((cosine + 1.0) / 2.0)  # normalize to 0..1
        return SignalScore(
            name="semantic",
            score=score,
            weight=weight,
            confidence=1.0,
            details={"cosine_similarity": round(cosine, 6), "embedding_model": llm_service.embedding_model()},
        )
    except Exception as exc:  # noqa: BLE001
        # Graceful degradation: keep pipeline alive if embedding infra is down.
        return SignalScore(
            name="semantic",
            score=0.5,
            weight=weight,
            confidence=0.0,
            details={"stage": "embedding", "error": str(exc)},
        )

