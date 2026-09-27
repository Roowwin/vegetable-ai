"""
Farmer Service
==============
Business logic for farmer operations including performance metrics.
"""

from decimal import Decimal
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.people import Farmer
from app.models.procurement import PurchaseOrder, PurchaseOrderItem, CollectionTrip
from app.models.inventory import Lot, Skid, Asset
from app.models.quality import QualityTest, Grade
from app.schemas.farmer import FarmerCreate, FarmerUpdate, FarmerPerformance
from app.services.base import BaseService


class FarmerService(BaseService[Farmer, FarmerCreate, FarmerUpdate]):
    """Service for managing farmer entities."""

    model = Farmer

    def __init__(self, db: Session):
        super().__init__(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: bool | None = None,
        location: str | None = None,
        min_rating: Decimal | None = None,
    ) -> tuple[list[Farmer], int]:
        """List farmers with optional filters."""
        query = self.db.query(Farmer)

        if is_active is not None:
            query = query.filter(Farmer.is_active == is_active)
        if location:
            query = query.filter(Farmer.location.ilike(f"%{location}%"))
        if min_rating is not None:
            query = query.filter(Farmer.rating >= min_rating)

        total = query.count()
        items = (
            query.order_by(Farmer.rating.desc().nullslast(), Farmer.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def get_performance(self, farmer_id: int) -> FarmerPerformance | None:
        """
        Compute performance metrics for a farmer.

        Metrics:
        - Total lots supplied
        - Total purchase value
        - Grade distribution across all assets
        - On-time delivery rate
        - Fill rate (received / expected)
        """
        farmer = self.get(farmer_id)
        if not farmer:
            return None

        # Get all lots from this farmer (via purchase orders)
        lots = (
            self.db.query(Lot)
            .join(PurchaseOrder, Lot.purchase_order_id == PurchaseOrder.id)
            .filter(PurchaseOrder.farmer_id == farmer_id)
            .all()
        )
        total_lots = len(lots)

        if total_lots == 0:
            return FarmerPerformance(
                farmer_id=farmer.id,
                farmer_name=farmer.name,
                total_lots=0,
                total_purchase_value=Decimal("0"),
                average_grade_distribution={},
                on_time_delivery_rate=0.0,
                fill_rate=0.0,
            )

        # Total purchase value
        total_value = sum(lot.acquisition_cost for lot in lots)

        # Grade distribution: collect grade codes from all asset-level quality tests
        grade_dist: dict[str, int] = {}
        for lot in lots:
            tests = (
                self.db.query(Grade.code)
                .join(QualityTest, QualityTest.grade_id == Grade.id)
                .join(Asset, QualityTest.asset_id == Asset.id)
                .join(Skid, Asset.skid_id == Skid.id)
                .filter(Skid.lot_id == lot.id)
                .all()
            )
            for (grade_code,) in tests:
                grade_dist[grade_code] = grade_dist.get(grade_code, 0) + 1

        # On-time delivery: count POs where actual <= expected delivery date
        on_time_pos, total_pos = self.db.query(
            func.sum(
                case(
                    (
                        PurchaseOrder.actual_delivery_date <= PurchaseOrder.expected_delivery_date,
                        1,
                    ),
                    else_=0,
                )
            ),
            func.count(PurchaseOrder.id),
        ).filter(
            PurchaseOrder.farmer_id == farmer_id,
            PurchaseOrder.status.in_(["FullyReceived", "PartiallyReceived"]),
            PurchaseOrder.actual_delivery_date.isnot(None),
            PurchaseOrder.expected_delivery_date.isnot(None),
        ).one()

        on_time_rate = (on_time_pos or 0) / total_pos if total_pos and total_pos > 0 else 0.0

        # Fill rate: average of (received / expected) across PO items
        # Use a CASE to avoid division by zero
        fill_rate_avg = self.db.query(
            func.avg(
                case(
                    (
                        PurchaseOrderItem.expected_quantity_kg > 0,
                        PurchaseOrderItem.received_quantity_kg / PurchaseOrderItem.expected_quantity_kg,
                    ),
                    else_=None,
                )
            )
        ).join(
            PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id
        ).filter(
            PurchaseOrder.farmer_id == farmer_id,
            PurchaseOrder.status.in_(["FullyReceived", "PartiallyReceived"]),
        ).scalar()

        fill_rate = float(fill_rate_avg) if fill_rate_avg is not None else 0.0

        return FarmerPerformance(
            farmer_id=farmer.id,
            farmer_name=farmer.name,
            total_lots=total_lots,
            total_purchase_value=total_value,
            average_grade_distribution=grade_dist,
            on_time_delivery_rate=round(on_time_rate, 3),
            fill_rate=round(fill_rate, 3),
        )
