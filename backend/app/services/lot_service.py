"""
Lot Service
===========
The heart of the business. Tracks lots from acquisition to sale and computes
the true profit and loss for each lot.

This is the most important service in the system.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import Lot, Skid, Asset, Inventory, InventoryTransaction
from app.models.people import Farmer
from app.models.quality import Grade, QualityTest, SortResult
from app.models.sales import SaleItem
from app.models.costs import CostEntry, LaborRecord
from app.schemas.lot import (
    LotBase, LotCreate, LotUpdate, LotRead, LotListItem,
    LotProfitLoss, CostBreakdown,
)
from app.services.base import BaseService


class LotService(BaseService[Lot, LotCreate, LotUpdate]):
    """Service for lot operations and P&L analysis."""

    model = Lot

    def __init__(self, db: Session):
        super().__init__(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        vegetable_id: int | None = None,
        farmer_id: int | None = None,
        min_acquired_at: datetime | None = None,
        max_acquired_at: datetime | None = None,
    ) -> tuple[list[Lot], int]:
        """List lots with optional filters."""
        query = self.db.query(Lot)

        if status:
            query = query.filter(Lot.status == status)
        if vegetable_id:
            query = query.filter(Lot.vegetable_id == vegetable_id)
        if farmer_id:
            query = query = query.join(
                __import__("app.models.procurement", fromlist=["PurchaseOrder"]).PurchaseOrder
            ).filter(
                __import__("app.models.procurement", fromlist=["PurchaseOrder"]).PurchaseOrder.farmer_id == farmer_id
            )
        if min_acquired_at:
            query = query.filter(Lot.acquired_at >= min_acquired_at)
        if max_acquired_at:
            query = query.filter(Lot.acquired_at <= max_acquired_at)

        total = query.count()
        items = query.order_by(Lot.acquired_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_code(self, lot_code: str) -> Lot | None:
        """Get a lot by its human-readable code (e.g., 'L-2024-00001')."""
        return self.db.query(Lot).filter(Lot.lot_code == lot_code).first()

    def compute_lot_pnl(self, lot_code: str) -> LotProfitLoss | None:
        """
        Compute detailed profit & loss for a single lot.

        This is the KILLER QUERY - answers "How much money did Lot L001 really make?"

        Breakdown includes:
        - Acquisition, transport, processing, storage, selling, waste costs
        - Revenue from all sales
        - Waste percentage and recovery value
        - Gross/net profit and margins (%, per kg)
        """
        lot = self.get_by_code(lot_code)
        if not lot:
            return None

        # ----- COSTS -----
        cost_records = (
            self.db.query(CostEntry)
            .filter(CostEntry.lot_id == lot.id)
            .all()
        )

        costs = CostBreakdown()
        for cr in cost_records:
            amount = cr.amount or Decimal("0")
            category = cr.cost_category or ""
            if category == "Acquisition":
                costs.acquisition += amount
            elif category == "Transport":
                costs.transport += amount
            elif category == "Processing":
                costs.processing += amount
            elif category == "Storage":
                costs.storage += amount
            elif category == "Selling":
                costs.selling += amount
            elif category == "Waste":
                costs.waste += amount
        costs.total = (
            costs.acquisition
            + costs.transport
            + costs.processing
            + costs.storage
            + costs.selling
            + costs.waste
        )

        # ----- REVENUE -----
        revenue_result = (
            self.db.query(func.coalesce(func.sum(SaleItem.line_total), 0))
            .filter(SaleItem.asset_id.in_(
                self.db.query(Asset.id).join(Skid, Asset.skid_id == Skid.id).filter(Skid.lot_id == lot.id)
            ))
            .one()
        )
        total_revenue = Decimal(str(revenue_result[0]))

        sold_weight_result = (
            self.db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
            .filter(SaleItem.asset_id.in_(
                self.db.query(Asset.id).join(Skid, Asset.skid_id == Skid.id).filter(Skid.lot_id == lot.id)
            ))
            .one()
        )
        sold_weight_kg = Decimal(str(sold_weight_result[0]))

        # ----- WASTE -----
        sort_result = (
            self.db.query(SortResult)
            .filter(SortResult.lot_id == lot.id)
            .first()
        )
        waste_kg = Decimal("0")
        waste_recovery_value = Decimal("0")
        if sort_result:
            waste_kg = (sort_result.damaged_kg or Decimal("0")) + (sort_result.recycle_kg or Decimal("0"))
            # Recovery: recycled items have minimal value, damaged items are a total loss
            if sort_result.recycle_kg and sort_result.recycle_kg > 0:
                waste_recovery_value = sort_result.recycle_kg * Decimal("0.05")  # $0.05/kg recovery

        waste_pct = (
            (waste_kg / lot.total_weight_kg * 100) if lot.total_weight_kg > 0 else Decimal("0")
        )

        # ----- PROFIT CALCULATIONS -----
        gross_profit = total_revenue - costs.total
        gross_margin_pct = (
            (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        )

        # Allocated overhead: lot's share of monthly overhead
        # For simplicity, we use 10% of acquisition cost as estimated overhead
        allocated_overhead = costs.acquisition * Decimal("0.10")
        net_profit = gross_profit - allocated_overhead
        net_margin_pct = (
            (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        )

        cost_per_kg = (
            costs.total / lot.total_weight_kg if lot.total_weight_kg > 0 else Decimal("0")
        )
        revenue_per_kg = (
            total_revenue / sold_weight_kg if sold_weight_kg > 0 else Decimal("0")
        )
        profit_per_kg = (
            net_profit / sold_weight_kg if sold_weight_kg > 0 else Decimal("0")
        )

        # ----- RELATED INFO -----
        farmer_name = "Unknown"
        if lot.purchase_order_id:
            from app.models.procurement import PurchaseOrder
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == lot.purchase_order_id).first()
            if po and po.farmer_id:
                farmer = self.db.query(Farmer).filter(Farmer.id == po.farmer_id).first()
                if farmer:
                    farmer_name = farmer.name

        vegetable_name = "Unknown"
        if lot.vegetable_id:
            from app.models.inventory import Vegetable
            veg = self.db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
            if veg:
                vegetable_name = veg.name

        return LotProfitLoss(
            lot_code=lot.lot_code,
            vegetable_name=vegetable_name,
            farmer_name=farmer_name,
            total_cost=costs,
            cost_per_kg=cost_per_kg,
            total_revenue=total_revenue,
            revenue_per_kg=revenue_per_kg,
            sold_weight_kg=sold_weight_kg,
            waste_kg=waste_kg,
            waste_pct=waste_pct,
            waste_recovery_value=waste_recovery_value,
            gross_profit=gross_profit,
            gross_margin_pct=gross_margin_pct,
            net_profit=net_profit,
            net_margin_pct=net_margin_pct,
            profit_per_kg=profit_per_kg,
            status=lot.status,
            acquired_at=lot.acquired_at,
            closed_at=None,
        )
