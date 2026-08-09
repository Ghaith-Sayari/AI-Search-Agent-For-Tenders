from config import config
from models.analysis import Analysis, Decision


def decide(analysis: Analysis) -> Analysis:
    """
    Applies thresholds to produce a final Decision. Mutates and returns
    the Analysis. Low-confidence analyses are always routed to REVIEW
    regardless of score -- a confident-looking number built on thin
    signal coverage is worse than an honest "needs a human".
    """
    thresholds = config.thresholds

    if analysis.low_confidence:
        analysis.decision = Decision.REVIEW
        analysis.reasoning = (
            analysis.reasoning
            or "Insufficient reliable signal coverage; routed to manual review."
        )
        return analysis

    if analysis.total_score >= thresholds.pursue:
        analysis.decision = Decision.PURSUE
    elif analysis.total_score <= thresholds.reject:
        analysis.decision = Decision.REJECT
    else:
        analysis.decision = Decision.REVIEW

    return analysis
