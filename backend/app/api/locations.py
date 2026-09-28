"""
Location Endpoints
==================
HTTP endpoints for physical location management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Annotated, Optional

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.services.location_service import LocationService

router = APIRouter(prefix="/api/locations", tags=["Locations"])


@router.get("", summary="List all locations")
async def list_locations(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    location_type: Optional[str] = Query(None, description="Filter by type: processing, storage, sales, etc."),
    is_active: Optional[bool] = Query(None),
):
    """List all physical locations in the shop."""
    service = LocationService(db)
    locations, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        location_type=location_type,
        is_active=is_active,
    )
    items = [
        {
            "id": loc.id,
            "code": loc.code,
            "name": loc.name,
            "location_type": loc.location_type,
            "temperature_zone": loc.temperature_zone,
            "capacity_kg": float(loc.capacity_kg) if loc.capacity_kg else None,
            "is_active": loc.is_active,
        }
        for loc in locations
    ]
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/{location_id}", summary="Get location details")
async def get_location(location_id: int, db: DbSession):
    """Get a single location by ID."""
    service = LocationService(db)
    loc = service.get(location_id)
    if not loc:
        raise not_found("Location", location_id)
    return {
        "id": loc.id,
        "code": loc.code,
        "name": loc.name,
        "location_type": loc.location_type,
        "temperature_zone": loc.temperature_zone,
        "capacity_kg": float(loc.capacity_kg) if loc.capacity_kg else None,
        "is_active": loc.is_active,
        "notes": loc.notes,
    }


@router.get("/{location_id}/contents", summary="What's at this location?")
async def get_location_contents(location_id: int, db: DbSession):
    """Get all lots and assets currently at this location."""
    service = LocationService(db)
    loc = service.get(location_id)
    if not loc:
        raise not_found("Location", location_id)
    return service.get_contents(location_id)


@router.get("/{location_id}/history", summary="Movement history for a location")
async def get_location_history(
    location_id: int,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
):
    """Get recent movement history (audit log) for a location."""
    service = LocationService(db)
    loc = service.get(location_id)
    if not loc:
        raise not_found("Location", location_id)

    history = service.get_history(location_id, limit=limit)
    return {
        "location_id": location_id,
        "location_code": loc.code,
        "event_count": len(history),
        "events": [
            {
                "asset_id": h.asset_id,
                "lot_id": h.lot_id,
                "from_location_id": h.from_location_id,
                "to_location_id": h.to_location_id,
                "moved_at": h.moved_at.isoformat() if h.moved_at else None,
                "moved_by": h.moved_by,
                "reason": h.reason,
                "notes": h.notes,
            }
            for h in history
        ],
    }
