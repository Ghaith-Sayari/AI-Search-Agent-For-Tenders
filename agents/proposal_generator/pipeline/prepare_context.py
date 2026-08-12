from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agents.proposal_generator.models.proposal_input import ProposalInput


@dataclass
class PreparedContext:
    tender_title: str
    source: str
    country: str
    description: str
    posting_date: datetime | None
    deadline: datetime | None
    url: str | None
    external_id: str | None
    company_name: str
    company_description: str
    sectors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    max_budget: float | None = None
    extracted_requirements: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


def _extract_requirements(description: str) -> list[str]:
    """Very first-pass requirement extraction from tender text."""
    lines = [line.strip(" -*\t") for line in description.splitlines()]
    candidates = [l for l in lines if l and any(k in l.lower() for k in ("must", "required", "shall", "deliver", "compliance"))]
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for item in candidates:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _derive_risk_flags(tender_country: str, profile_locations: list[str], deadline: datetime | None) -> list[str]:
    risks: list[str] = []

    if profile_locations and tender_country and tender_country not in profile_locations:
        risks.append("location_mismatch")

    if deadline is not None:
        now = datetime.utcnow().replace(tzinfo=None)
        dd = deadline.replace(tzinfo=None)
        days_left = (dd - now).days
        if days_left < 0:
            risks.append("deadline_passed")
        elif days_left <= 7:
            risks.append("short_timeline")

    return risks


def prepare_context(proposal_input: ProposalInput) -> PreparedContext:
    """Transform ProposalInput into normalized context consumed by drafting pipeline."""
    errors = proposal_input.validate()
    if errors:
        raise ValueError(f"Invalid ProposalInput: {'; '.join(errors)}")

    tender = proposal_input.tender
    profile = proposal_input.company_profile

    return PreparedContext(
        tender_title=tender.title,
        source=tender.source,
        country=tender.country,
        description=tender.description,
        posting_date=tender.posting_date,
        deadline=tender.deadline,
        url=tender.url,
        external_id=tender.external_id,
        company_name=profile.name,
        company_description=profile.description,
        sectors=profile.sectors,
        keywords=profile.keywords,
        locations=profile.locations,
        max_budget=profile.max_budget,
        extracted_requirements=_extract_requirements(tender.description),
        risk_flags=_derive_risk_flags(tender.country, profile.locations, tender.deadline),
    )


def context_as_prompt_payload(ctx: PreparedContext) -> dict[str, Any]:
    """Dict payload ready to inject into prompt templates."""
    return {
        "tender": {
            "title": ctx.tender_title,
            "source": ctx.source,
            "country": ctx.country,
            "description": ctx.description,
            "posting_date": ctx.posting_date.isoformat() if ctx.posting_date else None,
            "deadline": ctx.deadline.isoformat() if ctx.deadline else None,
            "url": ctx.url,
            "external_id": ctx.external_id,
            "requirements": ctx.extracted_requirements,
            "risk_flags": ctx.risk_flags,
        },
        "company_profile": {
            "name": ctx.company_name,
            "description": ctx.company_description,
            "sectors": ctx.sectors,
            "keywords": ctx.keywords,
            "locations": ctx.locations,
            "max_budget": ctx.max_budget,
        },
    }
