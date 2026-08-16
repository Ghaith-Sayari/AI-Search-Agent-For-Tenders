"""Service layer for company profile endpoints."""

from __future__ import annotations

from api.repositories.company_profile_repository import CompanyProfileRepository
from api.schemas.company_profile import CompanyProfile


class CompanyProfileService:
    def __init__(self, repository: CompanyProfileRepository | None = None) -> None:
        self.repository = repository or CompanyProfileRepository()

    def get_profile(self) -> CompanyProfile:
        row = self.repository.get()
        return CompanyProfile(**row)

    def update_profile(self, profile: CompanyProfile) -> CompanyProfile:
        row = self.repository.put(profile.model_dump())
        return CompanyProfile(**row)
