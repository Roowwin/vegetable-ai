"""
Sales Endpoints
===============
List, filter, and summarize sales transactions.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from typing import Annotated

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.sale import SaleCreate, SaleUpdate
from app.services.sale_service import SaleService

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.get("", summary="List sales")
async def list_sales(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    customer_id: int | None = Query(None),
    payment_method: str | None = Query(None),
    sold_after: datetime | None = Query(None),
    sold_before: datetime | None = Query(None),
):
    """List sales with filters and pagination."""
    service = SaleService(db)
    sales, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        status=status_filter,
        customer_id=customer_id,
        payment_method=payment_method,
        sold_after=sold_after,
        sold_before=sold_before,
    )
    items = []
    for sale in sales:
        items.append({
            "id": sale.id,
            "sale_code": sale.sale_code,
            "sold_at": sale.sold_at.isoformat(),
            "customer_id": sale.customer_id,
            "customer_name": sale.customer.name if sale.customer else None,
            "total_amount": float(sale.total_amount),
            "payment_method": sale.payment_method,
            "status": sale.status,
            "item_count": len(sale.items) if sale.items else 0,
        })
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/summary", summary="Get sales summary for a period")
async def get_sales_summary(
    db: DbSession,
    start: datetime = Query(..., description="Period start date"),
    end: datetime = Query(..., description="Period end date"),
):
    """Get aggregated sales stats for a date range."""
    service = SaleService(db)
    summary = service.get_summary(period_start=start, period_end=end)
    return {
        "period_start": summary.period_start.isoformat(),
        "period_end": summary.period_end.isoformat(),
        "total_sales": summary.total_sales,
        "total_revenue": float(summary.total_revenue),
        "total_items_sold": summary.total_items_sold,
        "average_sale_value": float(summary.average_sale_value),
        "top_customers": summary.top_customers,
        "top_vegetables": summary.top_vegetables,
        "payment_method_breakdown": summary.payment_method_breakdown,
    }


@router.get("/{sale_id}", summary="Get sale details")
async def get_sale(sale_id: int, db: DbSession):
    """Get a single sale with all its line items."""
    service = SaleService(db)
    sale = service.get(sale_id)
    if not sale:
        raise not_found("Sale", sale_id)
    return {
        "id": sale.id,
        "sale_code": sale.sale_code,
        "sold_at": sale.sold_at.isoformat(),
        "customer": {
            "id": sale.customer.id if sale.customer else None,
            "name": sale.customer.name if sale.customer else None,
        } if sale.customer else None,
        "status": sale.status,
        "payment_method": sale.payment_method,
        "subtotal": float(sale.subtotal),
        "tax": float(sale.tax),
        "discount": float(sale.discount),
        "total_amount": float(sale.total_amount),
        "items": [
            {
                "id": item.id,
                "vegetable_name": item.vegetable.name if item.vegetable else None,
                "grade_code": item.grade.code if item.grade else None,
                "quantity": float(item.quantity),
                "unit_type": item.unit_type,
                "unit_price": float(item.unit_price),
                "line_total": float(item.line_total),
            }
            for item in sale.items
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sale(data: SaleCreate, db: DbSession):
    """Create a new sale with line items."""
    service = SaleService(db)
    return service.create_with_items(data)
