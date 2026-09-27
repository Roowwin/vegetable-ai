"""
Purchase Order Service
======================
Procurement operations with supplier analytics.
"""

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.procurement import PurchaseOrder, PurchaseOrderItem
from app.models.people import Farmer
from app.models.inventory import Lot
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate, POItemCreate
from app.services.base import BaseService


class PurchaseOrderService(BaseService[PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate]):
    """Service for purchase order operations."""

    model = PurchaseOrder

    def __init__(self, db: Session):
        super().__init__(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        farmer_id: int | None = None,
        delivery_mode: str | None = None,
        issued_after: date | None = None,
        issued_before: date | None = None,
        overdue_only: bool = False,
    ) -> tuple[list[PurchaseOrder], int]:
        """List POs with optional filters."""
        query = self.db.query(PurchaseOrder)

        if status:
            query = query.filter(PurchaseOrder.status == status)
        if farmer_id:
            query = query.filter(PurchaseOrder.farmer_id == farmer_id)
        if delivery_mode:
            query = query.filter(PurchaseOrder.delivery_mode == delivery_mode)
        if issued_after:
            query = query.filter(PurchaseOrder.issue_date >= issued_after)
        if issued_before:
            query = query.filter(PurchaseOrder.issue_date <= issued_before)
        if overdue_only:
            today = date.today()
            query = query.filter(
                PurchaseOrder.expected_delivery_date < today,
                PurchaseOrder.status.in_(["Issued", "Acknowledged", "PartiallyReceived"]),
            )

        total = query.count()
        items = query.order_by(PurchaseOrder.issue_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def create_with_items(self, data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a PO with line items in one transaction."""
        po_data = data.model_dump(exclude={"items"})
        po = PurchaseOrder(**po_data)
        self.db.add(po)
        self.db.flush()

        for item_data in data.items:
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                **item_data.model_dump(),
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(po)
        return po

    def get_overdue(self) -> "list[PurchaseOrder]":
        """Get POs past expected delivery that aren't fully received."""
        today = date.today()
        return (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.expected_delivery_date < today,
                PurchaseOrder.status.in_(["Issued", "Acknowledged", "PartiallyReceived"]),
            )
            .all()
        )

    def get_open_value_by_farmer(self) -> "list[dict]":
        """Get total open PO value per farmer (for procurement planning)."""
        results = (
            self.db.query(
                Farmer.id,
                Farmer.name,
                func.count(PurchaseOrder.id).label("open_count"),
                func.coalesce(func.sum(PurchaseOrder.total_expected_value), 0).label("open_value"),
            )
            .join(PurchaseOrder, PurchaseOrder.farmer_id == Farmer.id)
            .filter(
                PurchaseOrder.status.in_(["Issued", "Acknowledged", "PartiallyReceived"]),
            )
            .group_by(Farmer.id, Farmer.name)
            .order_by(func.sum(PurchaseOrder.total_expected_value).desc())
            .all()
        )
        return [
            {
                "farmer_id": fid,
                "farmer_name": name,
                "open_pos": count,
                "open_value": float(value),
            }
            for fid, name, count, value in results
        ]
