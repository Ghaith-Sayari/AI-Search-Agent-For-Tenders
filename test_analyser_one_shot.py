import json
import sys
from pathlib import Path


def OpportunityAnalyser(tender_data: dict, company_profile: dict) -> dict:
    """
    One-shot analysis pipeline using the local opportunity_analyzer LLM service.
    Returns a dictionary with extraction + fit analysis status and payloads.
    """
    project_root = Path(__file__).resolve().parent
    analyzer_root = project_root / "agents" / "opportunity_analyzer"
    sys.path.insert(0, str(analyzer_root))

    from analyzers import keyword_analyzer, location_analyzer
    from models.analysis import Analysis, SignalScore
    from models.opportunity import Opportunity
    from models.profile import Profile
    from scoring.decision import decide
    from scoring.scorer import score_analysis
    from scoring.weights import weight_for
    from services import llm_service  # imported after path setup

    raw_text = tender_data.get("raw_text")
    if isinstance(raw_text, str) and raw_text.strip():
        tender_text = raw_text.strip()
    else:
        # Build a robust fallback text from structured tender fields
        fallback_parts = [
            f"Title: {tender_data.get('title', '')}".strip(),
            f"Country: {tender_data.get('country', '')}".strip(),
            f"Description: {tender_data.get('description', '')}".strip(),
        ]
        tender_text = "\n".join(
            p for p in fallback_parts
            if p and not p.endswith(":")
        ).strip()
    if not tender_text:
        raise ValueError("Tender data must include 'raw_text' or 'description'.")

    profile_text_parts = [
        company_profile.get("description", ""),
        "Sectors: " + ", ".join(company_profile.get("sectors", [])),
        "Keywords: " + ", ".join(company_profile.get("keywords", [])),
        "Locations: " + ", ".join(company_profile.get("locations", [])),
    ]
    profile_text = "\n".join(p for p in profile_text_parts if p and p.strip())
    if not profile_text.strip():
        raise ValueError("Company profile must include at least one descriptive field.")

    extraction = llm_service.extract(tender_text)

    # Proceed with fit analysis even if extraction is weak; analyzer returns status metadata.
    extracted_payload = extraction.data if extraction.data else {"raw": extraction.raw_text}
    fit = llm_service.analyze_fit(profile_text, extracted_payload)

    # Build typed domain objects for combined scoring path
    opportunity = Opportunity(
        id=str(tender_data.get("id", "")),
        title=str(tender_data.get("title", "")),
        country=str(tender_data.get("country", "")),
        description=str(tender_data.get("description", "")),
        raw_text=tender_data.get("raw_text") if isinstance(tender_data.get("raw_text"), str) else None,
    )
    profile = Profile(
        id=str(company_profile.get("id", "")),
        name=str(company_profile.get("name", "")),
        description=str(company_profile.get("description", "")),
        sectors=company_profile.get("sectors", []) if isinstance(company_profile.get("sectors"), list) else [],
        keywords=company_profile.get("keywords", []) if isinstance(company_profile.get("keywords"), list) else [],
        locations=company_profile.get("locations", []) if isinstance(company_profile.get("locations"), list) else [],
    )

    def _clamp01(value: object, default: float) -> float:
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, parsed))

    analysis = Analysis(opportunity_id=opportunity.id, profile_id=profile.id)
    analysis.add_signal(keyword_analyzer.analyze(opportunity, profile, weight_for("keyword")))
    analysis.add_signal(location_analyzer.analyze(opportunity, profile, weight_for("location")))
    # Reuse the SAME fit result already computed above to avoid run-to-run drift
    # from making an additional LLM call for llm_judgment.
    if fit.is_usable and isinstance(fit.data, dict):
        llm_signal = SignalScore(
            name="llm_judgment",
            score=_clamp01(fit.data.get("fit_score"), 0.5),
            weight=weight_for("llm_judgment"),
            confidence=_clamp01(fit.data.get("confidence"), 0.0),
            details={
                "reasoning": fit.data.get("reasoning", ""),
                "red_flags": fit.data.get("red_flags", []),
                "extracted": extraction.data if isinstance(extraction.data, dict) else {},
            },
        )
    else:
        llm_signal = SignalScore(
            name="llm_judgment",
            score=0.5,
            weight=weight_for("llm_judgment"),
            confidence=0.0,
            details={"reason": "fit analysis unavailable", "status": fit.status.value, "error": fit.error},
        )

    analysis.add_signal(llm_signal)
    analysis = score_analysis(analysis)
    analysis = decide(analysis)

    return {
        "extraction": {
            "status": extraction.status.value,
            "error": extraction.error,
            "data": extraction.data,
        },
        "fit_analysis": {
            "status": fit.status.value,
            "error": fit.error,
            "data": fit.data,
        },
        "combined_analysis": {
            "total_score": analysis.total_score,
            "decision": analysis.decision.value,
            "low_confidence": analysis.low_confidence,
            "reasoning": analysis.reasoning,
            "signals": [
                {
                    "name": s.name,
                    "score": s.score,
                    "weight": s.weight,
                    "confidence": s.confidence,
                    "weighted_score": round(s.weighted_score, 4),
                    "details": s.details,
                }
                for s in analysis.signals
            ],
        },
    }


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    base = Path(__file__).resolve().parent
    tender_file = base / "tender_offer.json"
    profile_file = base / "company_profile.json"

    try:
        if not tender_file.exists() or not profile_file.exists():
            missing = [str(p.name) for p in [tender_file, profile_file] if not p.exists()]
            raise FileNotFoundError(f"Missing required input file(s): {', '.join(missing)}")

        tender_data = load_json(tender_file)
        profile_data = load_json(profile_file)

        result = OpportunityAnalyser(tender_data, profile_data)

        print("=== Bid Analysis Result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
