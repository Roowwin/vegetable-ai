"""
Inventory Endpoints
===================
Current stock management and transactions.
"""

from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Query, status, Depends
from typing import Annotated

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryTransactionCreate,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("", summary="List inventory")
async def list_inventory(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    is_available: bool | None = Query(None),
    location: str | None = Query(None),
    vegetable_id: int | None = Query(None),
    expiring_within_days: int | None = Query(None, ge=0, le=365),
):
    """List current inventory with filters."""
    service = InventoryService(db)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        is_available=is_available,
        location=location,
        vegetable_id=vegetable_id,
        expiring_within_days=expiring_within_days,
    )
    return paginated_response(
        [
            {
                "id": inv.id,
                "location": inv.location,
                "quantity_kg": float(inv.quantity_kg) if inv.quantity_kg else None,
                "quantity_units": inv.quantity_units,
                "is_available": inv.is_available,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            }
            for inv in items
        ],
        total,
        pagination.skip,
        pagination.limit,
    )


@router.get("/total-value", summary="Get total inventory value")
async def get_total_value(db: DbSession):
    """Calculate total inventory value at cost."""
    service = InventoryService(db)
    value = service.get_total_value()
    return {"total_value": float(value), "currency": "USD"}


@router.get("/expiring", summary="Get items expiring soon")
async def get_expiring_soon(days: int = Query(7, ge=1, le=90), db: DbSession = None):
    """Get inventory items expiring within N days (default 7)."""
    service = InventoryService(db)
    items = service.get_expiring_soon(days=days)
    return {
        "days": days,
        "count": len(items),
        "items": [
            {
                "id": inv.id,
                "location": inv.location,
                "quantity_kg": float(inv.quantity_kg) if inv.quantity_kg else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            }
            for inv in items
        ],
    }


@router.get("/{inventory_id}", summary="Get inventory item")
async def get_inventory_item(inventory_id: int, db: DbSession):
    """Get a single inventory item."""
    service = InventoryService(db)
    item = service.get(inventory_id)
    if not item:
        raise not_found("Inventory", inventory_id)
    return item


@router.post("/{inventory_id}/transactions", status_code=status.HTTP_201_CREATED)
async def record_transaction(inventory_id: int, data: InventoryTransactionCreate, db: DbSession):
    """Record an inventory transaction (Received, Sold, Adjustment, etc.)."""
    service = InventoryService(db)
    try:
        txn = service.record_transaction(
            inventory_id=inventory_id,
            txn_type=data.txn_type,
            qty_change_kg=data.qty_change_kg,
            qty_change_units=data.qty_change_units,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            notes=data.notes,
        )
        return {
            "transaction_id": txn.id,
            "inventory_id": txn.inventory_id,
            "txn_type": txn.txn_type,
            "qty_change_kg": float(txn.qty_change_kg) if txn.qty_change_kg else None,
            "created_at": txn.created_at.isoformat(),
        }
    except ValueError as e:
        raise not_found("Inventory", inventory_id)
