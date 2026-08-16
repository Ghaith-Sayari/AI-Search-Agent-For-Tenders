"""Schemas for proposal engine endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ProposalStatus = Literal[
    "DRAFT",
    "GENERATING",
    "READY_FOR_REVIEW",
    "IN_REVIEW",
    "APPROVED",
    "EXPORTED",
    "FAILED",
]
SectionStatus = Literal["GENERATED", "EDITED", "REGENERATING"]
SectionAction = Literal["Regenerate", "Improve", "Shorten", "Expand"]


class ProposalConfig(BaseModel):
    title: str
    companyProfileId: str
    companyProfileName: str | None = None
    language: str = "en"
    proposalType: str = "technical"
    tone: str = "professional"
    additionalInstructions: str = ""


class ProposalSectionDTO(BaseModel):
    id: str
    title: str
    content: str
    status: SectionStatus = "GENERATED"
    lastUpdated: str | None = None


class ProposalQualityMetrics(BaseModel):
    tenderAlignment: float = 0.0
    requirementCoverage: float = 0.0
    companyCapabilityAlignment: float = 0.0
    missingInformation: list[str] = Field(default_factory=list)
    aiConfidence: float = 0.0


class RequirementsSummary(BaseModel):
    keyRequirements: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)


class Proposal(BaseModel):
    id: str
    opportunityId: str | None = None
    opportunityTitle: str = ""
    country: str = ""
    source: str = ""
    deadline: str | None = None
    overallScore: float = 0.0
    decision: str = "review"
    status: ProposalStatus = "DRAFT"
    config: ProposalConfig
    sections: list[ProposalSectionDTO] = Field(default_factory=list)
    qualityMetrics: ProposalQualityMetrics = Field(default_factory=ProposalQualityMetrics)
    requirementsSummary: RequirementsSummary = Field(default_factory=RequirementsSummary)


class CreateProposalPayload(BaseModel):
    opportunityId: str
    proposalTitle: str
    companyProfileId: str
    language: str = "en"
    proposalType: str = "technical"
    tone: str = "professional"
    additionalInstructions: str = ""


class RegenerateSectionPayload(BaseModel):
    action: SectionAction


class ExportProposalPayload(BaseModel):
    format: Literal["pdf", "docx", "markdown"] = "markdown"


class ExportProposalResponse(BaseModel):
    fileName: str
    fileUrl: str


class ProposalConfigPatch(BaseModel):
    title: str | None = None
    companyProfileId: str | None = None
    companyProfileName: str | None = None
    language: str | None = None
    proposalType: str | None = None
    tone: str | None = None
    additionalInstructions: str | None = None


class ProposalSectionPatch(BaseModel):
    id: str
    title: str | None = None
    content: str | None = None
    status: SectionStatus | None = None
    lastUpdated: str | None = None


class ProposalPatch(BaseModel):
    status: ProposalStatus | None = None
    decision: str | None = None
    overallScore: float | None = Field(default=None, ge=0, le=100)
    config: ProposalConfigPatch | None = None
    sections: list[ProposalSectionPatch] | None = None
    executiveSummary: str | None = None
