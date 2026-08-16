"""Mapper between generated_proposal rows and frontend proposal DTO."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.schemas.proposals import (
    Proposal,
    ProposalConfig,
    ProposalQualityMetrics,
    ProposalSectionDTO,
    RequirementsSummary,
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_row_to_proposal(row: dict[str, Any]) -> Proposal:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    sections_raw = row.get("sections") if isinstance(row.get("sections"), list) else []
    sections = [
        ProposalSectionDTO(
            id=str(s.get("key") or s.get("id") or f"section-{idx+1}"),
            title=str(s.get("title") or f"Section {idx+1}"),
            content=str(s.get("content") or ""),
            status=str(s.get("status") or "GENERATED"),
            lastUpdated=str(s.get("lastUpdated") or row.get("updated_at") or _iso_now()),
        )
        for idx, s in enumerate(sections_raw)
        if isinstance(s, dict)
    ]

    confidence = float(row.get("confidence_score") or 0.0) * 100.0
    compliance_issues = row.get("compliance_issues") if isinstance(row.get("compliance_issues"), list) else []
    quality = ProposalQualityMetrics(
        tenderAlignment=min(100.0, max(0.0, float(row.get("total_score") or 0.0) * 100.0)),
        requirementCoverage=max(0.0, 100.0 - (len(compliance_issues) * 10.0)),
        companyCapabilityAlignment=min(100.0, max(0.0, float(row.get("total_score") or 0.0) * 100.0)),
        missingInformation=[str(i.get("message")) for i in compliance_issues if isinstance(i, dict) and i.get("message")],
        aiConfidence=confidence,
    )

    req_summary = RequirementsSummary(
        keyRequirements=metadata.get("key_requirements", []) if isinstance(metadata.get("key_requirements"), list) else [],
        eligibility=metadata.get("eligibility", []) if isinstance(metadata.get("eligibility"), list) else [],
        deliverables=metadata.get("deliverables", []) if isinstance(metadata.get("deliverables"), list) else [],
        deadlines=metadata.get("deadlines", []) if isinstance(metadata.get("deadlines"), list) else [],
    )

    config = ProposalConfig(
        title=str(metadata.get("proposal_title") or metadata.get("tender_title") or "Generated Proposal"),
        companyProfileId=str(metadata.get("company_profile_id") or "default"),
        companyProfileName=str(row.get("profile_name") or metadata.get("company_profile_name") or ""),
        language=str(metadata.get("language") or "en"),
        proposalType=str(metadata.get("proposal_type") or "technical"),
        tone=str(metadata.get("tone") or "professional"),
        additionalInstructions=str(metadata.get("additional_instructions") or ""),
    )

    raw_status = str(metadata.get("status") or "READY_FOR_REVIEW").upper()
    allowed = {"DRAFT", "GENERATING", "READY_FOR_REVIEW", "IN_REVIEW", "APPROVED", "EXPORTED", "FAILED"}
    status = raw_status if raw_status in allowed else "READY_FOR_REVIEW"

    return Proposal(
        id=str(row.get("id")),
        opportunityId=str(metadata.get("opportunity_id") or row.get("tender_external_id") or ""),
        opportunityTitle=str(metadata.get("tender_title") or config.title),
        country=str(metadata.get("country") or ""),
        source=str(metadata.get("source") or ""),
        deadline=str(metadata.get("deadline") or ""),
        overallScore=min(100.0, max(0.0, float(row.get("total_score") or 0.0) * 100.0)),
        decision=str(row.get("decision") or "review"),
        status=status,  # type: ignore[arg-type]
        config=config,
        sections=sections,
        qualityMetrics=quality,
        requirementsSummary=req_summary,
    )
