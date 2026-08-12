"""
Combines individual SignalScores into a single 0..1 total score.

Key behavior: a signal with low confidence is excluded and its weight is
redistributed proportionally across the remaining usable signals. This keeps
flaky/misconfigured signals from quietly corrupting the total.

Current configured signals:
- keyword
- location
- llm_judgment (with an additional min_llm_confidence gate from config)
"""

from agents.opportunity_analyzer.config import config
from agents.opportunity_analyzer.models.analysis import Analysis, SignalScore

# Below this confidence, a signal is excluded and its weight redistributed.
CONFIDENCE_FLOOR = 0.15


def _is_usable_signal(signal: SignalScore) -> bool:
    """
    Decides whether a signal is usable for scoring.

    Special rule: llm_judgment must meet config.thresholds.min_llm_confidence.
    Other signals use CONFIDENCE_FLOOR.
    """
    if signal.name == "llm_judgment":
        return signal.confidence >= max(CONFIDENCE_FLOOR, config.thresholds.min_llm_confidence)
    return signal.confidence >= CONFIDENCE_FLOOR


def compute_total_score(signals: list[SignalScore]) -> tuple[float, bool]:
    """
    Returns (total_score, low_confidence_flag).
    low_confidence_flag is True if we had to drop enough signals that the
    remaining weight coverage is thin (<50% of original weight).
    """
    if not signals:
        return 0.0, True

    usable = [s for s in signals if _is_usable_signal(s)]
    original_weight_total = sum(s.weight for s in signals)
    usable_weight_total = sum(s.weight for s in usable)

    if usable_weight_total == 0:
        return 0.5, True  # nothing usable -- neutral score, flag for review

    total = sum(s.score * s.weight for s in usable) / usable_weight_total
    low_confidence = (usable_weight_total / original_weight_total) < 0.5

    return round(total, 4), low_confidence


def score_analysis(analysis: Analysis) -> Analysis:
    """Mutates and returns the Analysis with total_score and low_confidence set."""
    total, low_confidence = compute_total_score(analysis.signals)
    analysis.total_score = total
    analysis.low_confidence = low_confidence
    return analysis
