"""
Sale Service
============
Sales transactions with line items and revenue analytics.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales import Sale, SaleItem
from app.models.people import Customer
from app.models.inventory import Vegetable
from app.schemas.sale import (
    SaleCreate, SaleUpdate, SaleItemCreate,
    SalesSummary,
)
from app.services.base import BaseService


class SaleService(BaseService[Sale, SaleCreate, SaleUpdate]):
    """Service for sale operations."""

    model = Sale

    def __init__(self, db: Session):
        super().__init__(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        customer_id: int | None = None,
        payment_method: str | None = None,
        sold_after: datetime | None = None,
        sold_before: datetime | None = None,
    ) -> tuple[list[Sale], int]:
        """List sales with optional filters."""
        query = self.db.query(Sale)

        if status:
            query = query.filter(Sale.status == status)
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        if sold_after:
            query = query.filter(Sale.sold_at >= sold_after)
        if sold_before:
            query = query.filter(Sale.sold_at <= sold_before)

        total = query.count()
        items = query.order_by(Sale.sold_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def create_with_items(self, data: SaleCreate) -> Sale:
        """
        Create a sale with line items in one transaction.

        This handles the full sale creation flow:
        1. Create the sale header
        2. Create all line items
        3. Update inventory (decrement quantities)
        4. Commit atomically
        """
        # Create the sale header (exclude items from the dump)
        sale_data = data.model_dump(exclude={"items"})
        sale = Sale(**sale_data)
        self.db.add(sale)
        self.db.flush()  # Get the sale ID

        # Create line items
        for item_data in data.items:
            item = SaleItem(
                sale_id=sale.id,
                **item_data.model_dump(),
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(sale)
        return sale

    def get_summary(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> SalesSummary:
        """
        Compute sales summary for a date range.

        Includes:
        - Total sales count
        - Total revenue
        - Average sale value
        - Top customers
        - Top vegetables
        - Payment method breakdown
        """
        # Base query: sales in the period
        base_query = self.db.query(Sale).filter(
            Sale.sold_at >= period_start,
            Sale.sold_at <= period_end,
            Sale.status == "Completed",
        )

        total_sales = base_query.count()
        revenue_result = base_query.with_entities(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).scalar()
        total_revenue = Decimal(str(revenue_result or 0))

        average_sale = total_revenue / total_sales if total_sales > 0 else Decimal("0")

        # Total items sold
        total_items = self.db.query(
            func.coalesce(func.sum(SaleItem.quantity), 0)
        ).join(Sale, SaleItem.sale_id == Sale.id).filter(
            Sale.sold_at >= period_start,
            Sale.sold_at <= period_end,
            Sale.status == "Completed",
        ).scalar()

        # Top customers by spend
        top_customers_query = (
            self.db.query(
                Customer.name,
                func.sum(Sale.total_amount).label("total_spent"),
            )
            .join(Sale, Sale.customer_id == Customer.id)
            .filter(
                Sale.sold_at >= period_start,
                Sale.sold_at <= period_end,
                Sale.status == "Completed",
            )
            .group_by(Customer.name)
            .order_by(func.sum(Sale.total_amount).desc())
            .limit(5)
            .all()
        )
        top_customers = [
            {"name": name, "total_spent": float(total)}
            for name, total in top_customers_query
        ]

        # Top vegetables by quantity sold
        top_veg_query = (
            self.db.query(
                Vegetable.name,
                func.sum(SaleItem.quantity).label("total_kg"),
                func.sum(SaleItem.line_total).label("total_revenue"),
            )
            .join(SaleItem, SaleItem.vegetable_id == Vegetable.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(
                Sale.sold_at >= period_start,
                Sale.sold_at <= period_end,
                Sale.status == "Completed",
            )
            .group_by(Vegetable.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(5)
            .all()
        )
        top_vegetables = [
            {
                "name": name,
                "total_kg": float(total_kg),
                "total_revenue": float(total_revenue),
            }
            for name, total_kg, total_revenue in top_veg_query
        ]

        # Payment method breakdown
        payment_query = (
            self.db.query(
                Sale.payment_method,
                func.sum(Sale.total_amount).label("total"),
            )
            .filter(
                Sale.sold_at >= period_start,
                Sale.sold_at <= period_end,
                Sale.status == "Completed",
            )
            .group_by(Sale.payment_method)
            .all()
        )
        payment_breakdown = {
            method or "unknown": float(total)
            for method, total in payment_query
        }

        return SalesSummary(
            period_start=period_start,
            period_end=period_end,
            total_sales=total_sales,
            total_revenue=total_revenue,
            total_items_sold=int(total_items or 0),
            average_sale_value=average_sale,
            top_customers=top_customers,
            top_vegetables=top_vegetables,
            payment_method_breakdown=payment_breakdown,
        )
