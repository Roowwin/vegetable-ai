"""
Farmer Endpoints
================
CRUD operations plus performance analytics.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Annotated

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.farmer import (
    FarmerCreate, FarmerUpdate, FarmerRead, FarmerListItem, FarmerPerformance,
)
from app.services.farmer_service import FarmerService

router = APIRouter(prefix="/api/farmers", tags=["Farmers"])


@router.get("", summary="List farmers")
async def list_farmers(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    is_active: bool | None = Query(None, description="Filter by active status"),
    location: str | None = Query(None, description="Filter by location (partial match)"),
    min_rating: float | None = Query(None, ge=0, le=5, description="Minimum rating"),
):
    """List farmers with optional filters and pagination."""
    from decimal import Decimal
    service = FarmerService(db)
    farmers, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        is_active=is_active,
        location=location,
        min_rating=Decimal(str(min_rating)) if min_rating is not None else None,
    )
    # Return lightweight list items for performance
    items = [FarmerListItem.model_validate(f) for f in farmers]
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/{farmer_id}", response_model=FarmerRead, summary="Get farmer details")
async def get_farmer(farmer_id: int, db: DbSession):
    """Get a single farmer by ID."""
    service = FarmerService(db)
    farmer = service.get(farmer_id)
    if not farmer:
        raise not_found("Farmer", farmer_id)
    return farmer


@router.get("/{farmer_id}/performance", response_model=FarmerPerformance, summary="Get farmer performance metrics")
async def get_farmer_performance(farmer_id: int, db: DbSession):
    """Get computed performance metrics for a farmer (lots, value, on-time %, fill rate)."""
    service = FarmerService(db)
    perf = service.get_performance(farmer_id)
    if not perf:
        raise not_found("Farmer", farmer_id)
    return perf


@router.post("", response_model=FarmerRead, status_code=status.HTTP_201_CREATED, summary="Create farmer")
async def create_farmer(data: FarmerCreate, db: DbSession):
    """Create a new farmer."""
    service = FarmerService(db)
    farmer = service.create(data)
    return farmer


@router.patch("/{farmer_id}", response_model=FarmerRead, summary="Update farmer")
async def update_farmer(farmer_id: int, data: FarmerUpdate, db: DbSession):
    """Update a farmer (partial update - only provided fields are changed)."""
    service = FarmerService(db)
    farmer = service.update(farmer_id, data)
    if not farmer:
        raise not_found("Farmer", farmer_id)
    return farmer


@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete farmer")
async def delete_farmer(farmer_id: int, db: DbSession, hard: bool = Query(False, description="Hard delete (vs soft)")):
    """Delete a farmer. Soft delete by default (sets is_active=False)."""
    service = FarmerService(db)
    if hard:
        success = service.hard_delete(farmer_id)
    else:
        success = service.soft_delete(farmer_id)
    if not success:
        raise not_found("Farmer", farmer_id)
    return None
