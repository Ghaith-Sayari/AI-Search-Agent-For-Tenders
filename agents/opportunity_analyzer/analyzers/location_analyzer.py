"""Rule-based location match. Treats an empty profile location list as 'anywhere is fine'."""

from agents.opportunity_analyzer.models.analysis import SignalScore
from agents.opportunity_analyzer.models.opportunity import Opportunity
from agents.opportunity_analyzer.models.profile import Profile


def analyze(opportunity: Opportunity, profile: Profile, weight: float) -> SignalScore:
    if not profile.locations:
        # No location constraints configured -- everything passes.
        return SignalScore(name="location", score=1.0, weight=weight, confidence=1.0,
                            details={"reason": "no location constraint on profile"})

    if not opportunity.country:
        return SignalScore(name="location", score=0.5, weight=weight, confidence=0.0,
                            details={"reason": "opportunity has no country"})

    opp_country = opportunity.country.lower().strip()
    profile_countries = [c.lower().strip() for c in profile.locations]

    if any(pc == opp_country for pc in profile_countries):
        return SignalScore(name="location", score=1.0, weight=weight, confidence=1.0,
                            details={"match_type": "exact"})

    return SignalScore(name="location", score=0.0, weight=weight, confidence=1.0,
                        details={"match_type": "none"})
