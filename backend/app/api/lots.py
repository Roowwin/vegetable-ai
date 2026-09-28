"""
Lot Endpoints
=============
CRUD operations plus the killer P&L endpoint.

The /pnl endpoint is what makes VeggieOps AI valuable to a shop owner.
"""

from datetime import datetime
from fastapi import APIRouter, Query, status, Depends
from typing import Annotated
from pydantic import BaseModel, Field


from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.lot import (
    LotCreate, LotUpdate, LotRead, LotListItem, LotProfitLoss,
)
from app.services.lot_service import LotService

router = APIRouter(prefix="/api/lots", tags=["Lots"])


@router.get("", summary="List lots")
async def list_lots(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    status: str | None = Query(None, description="Filter by lot status"),
    vegetable_id: int | None = Query(None),
    farmer_id: int | None = Query(None),
    min_acquired_at: datetime | None = Query(None),
    max_acquired_at: datetime | None = Query(None),
):
    """List lots with filters and pagination."""
    service = LotService(db)
    lots, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        status=status,
        vegetable_id=vegetable_id,
        farmer_id=farmer_id,
        min_acquired_at=min_acquired_at,
        max_acquired_at=max_acquired_at,
    )
    items = []
    for lot in lots:
        # Build list item with vegetable and farmer names if available
        veg_name = lot.vegetable.name if lot.vegetable else None
        farmer_name = None
        if lot.purchase_order and lot.purchase_order.farmer:
            farmer_name = lot.purchase_order.farmer.name
        items.append(LotListItem(
            id=lot.id,
            lot_code=lot.lot_code,
            vegetable_id=lot.vegetable_id,
            vegetable_name=veg_name,
            farmer_id=lot.purchase_order.farmer_id if lot.purchase_order else None,
            farmer_name=farmer_name,
            acquired_at=lot.acquired_at,
            total_weight_kg=lot.total_weight_kg,
            acquisition_cost=lot.acquisition_cost,
            status=lot.status,
            image_url=None,  # Deferred to later
        ))
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/{lot_code}", response_model=LotRead, summary="Get lot details")
async def get_lot(lot_code: str, db: DbSession):
    """Get a single lot by its code (e.g., 'L-2024-00001')."""
    service = LotService(db)
    lot = service.get_by_code(lot_code)
    if not lot:
        raise not_found("Lot", lot_code)
    return lot


@router.get("/{lot_code}/pnl", response_model=LotProfitLoss, summary="Get lot profit & loss breakdown")
async def get_lot_pnl(lot_code: str, db: DbSession):
    """
    Compute detailed profit & loss for a single lot.

    Returns the complete financial breakdown:
    - Cost breakdown by category (acquisition, transport, processing, storage)
    - Revenue from all sales
    - Waste percentage
    - Gross profit, net profit, margins (gross, net, per kg)

    This is the KILLER QUERY - answers 'How much money did Lot L001 really make?'
    """
    service = LotService(db)
    pnl = service.compute_lot_pnl(lot_code)
    if not pnl:
        raise not_found("Lot", lot_code)
    return pnl


@router.post("", response_model=LotRead, status_code=status.HTTP_201_CREATED)
async def create_lot(data: LotCreate, db: DbSession):
    """Create a new lot."""
    service = LotService(db)
    return service.create(data)


@router.patch("/{lot_code}", response_model=LotRead)
async def update_lot(lot_code: str, data: LotUpdate, db: DbSession):
    """Update a lot (e.g., change status, add notes)."""
    service = LotService(db)
    lot = service.get_by_code(lot_code)
    if not lot:
        raise not_found("Lot", lot_code)
    # Use base service update with the lot's ID
    from app.services.base import BaseService
    base = BaseService(service.model, type(data), type(data))
    # Simpler: just call update directly via the service
    updated = service.update(lot.id, data)
    return updated
class MoveLotRequest(BaseModel):
    """Request to move a lot to a new location."""
    to_location_code: str = Field(description="Target location code (e.g., 'COLD_ROOM_A')")
    employee_id: int = Field(gt=0, description="ID of employee performing the move")
    reason: str = Field(default="Manual move", max_length=60)
    notes: str | None = Field(default=None, max_length=500)
@router.post("/{lot_code}/move", summary="Manually move a lot to a new location")
async def move_lot(lot_code: str, data: MoveLotRequest, db: DbSession):
    """
    Manually move a lot to a new location.
    
    Creates a LocationHistory record and updates the lot's current_location_id.
    Also moves all assets in the lot.
    """
    service = LotService(db)
    try:
        result = service.move_lot(
            lot_code=lot_code,
            to_location_code=data.to_location_code,
            employee_id=data.employee_id,
            reason=data.reason,
            notes=data.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "move_failed", "message": str(e)},
        )


@router.get("/{lot_code}/location-history", summary="Get location history for a lot")
async def get_lot_location_history(lot_code: str, db: DbSession, limit: int = 50):
    """Get all location movements for a lot (audit log)."""
    service = LotService(db)
    lot = service.get_by_code(lot_code)
    if not lot:
        raise not_found("Lot", lot_code)
    history = service.get_location_history(lot_code, limit=limit)
    return {
        "lot_code": lot_code,
        "current_location_id": lot.current_location_id,
        "event_count": len(history),
        "events": history,
    }
