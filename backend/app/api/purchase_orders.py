"""
Purchase Order Endpoints
========================
Procurement operations and analytics.
"""

from datetime import date
from fastapi import APIRouter, Depends, Query, status
from typing import Annotated

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])


@router.get("", summary="List purchase orders")
async def list_purchase_orders(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: str | None = Query(None, alias="status"),
    farmer_id: int | None = Query(None),
    delivery_mode: str | None = Query(None),
    issued_after: date | None = Query(None),
    issued_before: date | None = Query(None),
    overdue_only: bool = Query(False, description="Only show overdue POs"),
):
    """List purchase orders with filters."""
    service = PurchaseOrderService(db)
    pos, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        status=status_filter,
        farmer_id=farmer_id,
        delivery_mode=delivery_mode,
        issued_after=issued_after,
        issued_before=issued_before,
        overdue_only=overdue_only,
    )
    items = []
    for po in pos:
        is_overdue = False
        if po.expected_delivery_date and po.status in ["Issued", "Acknowledged", "PartiallyReceived"]:
            is_overdue = po.expected_delivery_date < date.today()
        items.append({
            "id": po.id,
            "po_number": po.po_number,
            "farmer_name": po.farmer.name if po.farmer else None,
            "status": po.status,
            "issue_date": po.issue_date.isoformat(),
            "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            "actual_delivery_date": po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
            "total_expected_value": float(po.total_expected_value),
            "total_actual_value": float(po.total_actual_value) if po.total_actual_value else None,
            "delivery_mode": po.delivery_mode,
            "is_overdue": is_overdue,
        })
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/overdue", summary="Get overdue purchase orders")
async def get_overdue_pos(db: DbSession):
    """Get POs past their expected delivery date that aren't fully received."""
    service = PurchaseOrderService(db)
    overdue = service.get_overdue()
    return {
        "count": len(overdue),
        "items": [
            {
                "id": po.id,
                "po_number": po.po_number,
                "farmer_name": po.farmer.name if po.farmer else None,
                "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                "days_overdue": (date.today() - po.expected_delivery_date).days if po.expected_delivery_date else 0,
                "total_expected_value": float(po.total_expected_value),
            }
            for po in overdue
        ],
    }


@router.get("/open-by-farmer", summary="Get open PO value grouped by farmer")
async def get_open_by_farmer(db: DbSession):
    """Get total open PO value per farmer (for procurement planning)."""
    service = PurchaseOrderService(db)
    return {"farmers": service.get_open_value_by_farmer()}


@router.get("/{po_id}", summary="Get purchase order details")
async def get_purchase_order(po_id: int, db: DbSession):
    """Get a single purchase order with line items."""
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise not_found("PurchaseOrder", po_id)
    return {
        "id": po.id,
        "po_number": po.po_number,
        "farmer": {
            "id": po.farmer.id if po.farmer else None,
            "name": po.farmer.name if po.farmer else None,
        } if po.farmer else None,
        "status": po.status,
        "issue_date": po.issue_date.isoformat(),
        "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
        "actual_delivery_date": po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
        "total_expected_value": float(po.total_expected_value),
        "total_actual_value": float(po.total_actual_value) if po.total_actual_value else None,
        "delivery_mode": po.delivery_mode,
        "payment_terms": po.payment_terms,
        "items": [
            {
                "id": item.id,
                "vegetable_name": item.vegetable.name if item.vegetable else None,
                "expected_quantity_kg": float(item.expected_quantity_kg),
                "received_quantity_kg": float(item.received_quantity_kg),
                "expected_unit_price": float(item.expected_unit_price),
                "fill_rate": float(item.received_quantity_kg / item.expected_quantity_kg) if item.expected_quantity_kg > 0 else 0,
            }
            for item in po.items
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_purchase_order(data: PurchaseOrderCreate, db: DbSession):
    """Create a new purchase order with line items."""
    service = PurchaseOrderService(db)
    return service.create_with_items(data)
