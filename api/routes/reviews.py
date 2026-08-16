"""Review queue API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.reviews import ResolveReviewRequest, ReviewItem
from api.services.review_service import ReviewService

router = APIRouter(prefix="/v1/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewItem])
async def get_reviews() -> list[ReviewItem]:
    service = ReviewService()
    return service.list_reviews()


@router.post("/{review_id}/resolve", response_model=ReviewItem)
async def resolve_review(review_id: str, payload: ResolveReviewRequest) -> ReviewItem:
    service = ReviewService()
    item = service.resolve_review(review_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail=f"Review item '{review_id}' not found")
    return item
