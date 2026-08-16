"""Schemas for company profile settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    id: str = "default"
    name: str = "Default Organization"
    description: str = ""
    primarySector: str = ""
    subSectors: list[str] = Field(default_factory=list)
    coreServices: list[str] = Field(default_factory=list)
    targetCountries: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    minContractValueEur: float | None = None
    maxContractValueEur: float | None = None
    gatekeeperMinScore: float = 50.0
    autoApproveThreshold: float = 75.0
