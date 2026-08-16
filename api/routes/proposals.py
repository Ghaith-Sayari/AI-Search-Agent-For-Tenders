"""Proposal engine API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.proposals import (
    CreateProposalPayload,
    ExportProposalPayload,
    ExportProposalResponse,
    Proposal,
    ProposalPatch,
    ProposalQualityMetrics,
    ProposalSectionDTO,
    RegenerateSectionPayload,
)
from api.services.proposal_service import ProposalGenerationError, ProposalService

router = APIRouter(prefix="/v1/proposals", tags=["proposals"])


@router.get("", response_model=list[Proposal])
async def get_proposals() -> list[Proposal]:
    return ProposalService().list_proposals()


@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(proposal_id: str) -> Proposal:
    proposal = ProposalService().get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return proposal


@router.post("", response_model=Proposal)
async def create_proposal(payload: CreateProposalPayload) -> Proposal:
    try:
        return ProposalService().create_proposal(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{proposal_id}/generate", response_model=Proposal)
async def generate_proposal(proposal_id: str) -> Proposal:
    try:
        proposal = ProposalService().generate_proposal(proposal_id)
    except ProposalGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return proposal


@router.patch("/{proposal_id}", response_model=Proposal)
async def patch_proposal(proposal_id: str, payload: ProposalPatch) -> Proposal:
    proposal = ProposalService().patch_proposal(proposal_id, payload)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return proposal


@router.post("/{proposal_id}/sections/{section_id}/regenerate", response_model=ProposalSectionDTO)
async def regenerate_section(
    proposal_id: str,
    section_id: str,
    payload: RegenerateSectionPayload,
) -> ProposalSectionDTO:
    section = ProposalService().regenerate_section(proposal_id, section_id, payload)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' or proposal '{proposal_id}' not found")
    return section


@router.get("/{proposal_id}/quality", response_model=ProposalQualityMetrics)
async def get_quality(proposal_id: str) -> ProposalQualityMetrics:
    quality = ProposalService().get_quality(proposal_id)
    if not quality:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return quality


@router.post("/{proposal_id}/export", response_model=ExportProposalResponse)
async def export_proposal(
    proposal_id: str,
    payload: ExportProposalPayload,
) -> ExportProposalResponse:
    result = ProposalService().export_proposal(proposal_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return result
