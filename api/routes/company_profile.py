"""Company profile settings API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.company_profile import CompanyProfile
from api.services.company_profile_service import CompanyProfileService

router = APIRouter(prefix="/v1/company-profile", tags=["company-profile"])


@router.get("", response_model=CompanyProfile)
async def get_company_profile() -> CompanyProfile:
    service = CompanyProfileService()
    try:
        return service.get_profile()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to read company profile: {exc}") from exc


@router.put("", response_model=CompanyProfile)
async def put_company_profile(payload: CompanyProfile) -> CompanyProfile:
    service = CompanyProfileService()
    try:
        return service.update_profile(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to save company profile: {exc}") from exc
