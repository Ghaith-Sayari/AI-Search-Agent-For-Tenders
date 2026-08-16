"""Company profile settings API routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas.company_profile import CompanyProfile
from api.services.company_profile_service import CompanyProfileService

router = APIRouter(prefix="/v1/company-profile", tags=["company-profile"])


@router.get("", response_model=CompanyProfile)
async def get_company_profile() -> CompanyProfile:
    service = CompanyProfileService()
    return service.get_profile()


@router.put("", response_model=CompanyProfile)
async def put_company_profile(payload: CompanyProfile) -> CompanyProfile:
    service = CompanyProfileService()
    return service.update_profile(payload)
