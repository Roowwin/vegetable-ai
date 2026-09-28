"""
Cost Calculation Service
========================
Centralized service for all cost calculations, allocation, and analysis.

Handles:
- Per-item cost allocation (distribute lot costs to individual assets)
- Cost comparison across vegetables
- Waste valuation
- Profitability metrics
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import Lot, Asset, Skid, Vegetable
from app.models.quality import Grade
from app.models.sales import Sale, SaleItem
from app.models.costs import CostEntry, LaborRecord
from app.models.people import Farmer


@dataclass
class CostBreakdownDetail:
    """Detailed cost breakdown for a lot."""
    acquisition: Decimal
    transport: Decimal
    processing: Decimal
    storage: Decimal
    selling: Decimal
    waste: Decimal
    total: Decimal


@dataclass
class ItemCost:
    """Cost assigned to a single asset/item."""
    asset_id: int
    asset_code: str
    weight_kg: Optional[Decimal]
    allocated_cost: Decimal
    cost_per_kg: Decimal
    share_of_lot_pct: Decimal  # What % of lot's total cost this item represents


@dataclass
class VegetableProfitability:
    """Profitability comparison for a vegetable type."""
    vegetable_id: int
    vegetable_name: str
    total_lots: int
    total_kg_acquired: Decimal
    total_kg_sold: Decimal
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    profit_per_kg: Decimal
    margin_pct: Decimal
    waste_pct: Decimal


@dataclass
class WasteValuation:
    """Value of wasted/recycled items."""
    lot_code: str
    vegetable_name: str
    waste_kg: Decimal
    damaged_kg: Decimal
    recycle_kg: Decimal
    cost_of_waste: Decimal  # What we paid for the waste
    potential_revenue: Decimal  # What we could have sold it for
    net_loss: Decimal  # Cost of waste minus recovery value


class CostService:
    """Service for cost calculations and analysis."""

    def __init__(self, db: Session):
        self.db = db

    def get_lot_cost_breakdown(self, lot_id: int) -> CostBreakdownDetail:
        """Get detailed cost breakdown for a lot by category."""
        records = self.db.query(CostEntry).filter(CostEntry.lot_id == lot_id).all()

        breakdown = CostBreakdownDetail(
            acquisition=Decimal("0"),
            transport=Decimal("0"),
            processing=Decimal("0"),
            storage=Decimal("0"),
            selling=Decimal("0"),
            waste=Decimal("0"),
            total=Decimal("0"),
        )

        for cr in records:
            amount = cr.amount or Decimal("0")
            category = cr.cost_category or ""
            if category == "Acquisition":
                breakdown.acquisition += amount
            elif category == "Transport":
                breakdown.transport += amount
            elif category == "Processing":
                breakdown.processing += amount
            elif category == "Storage":
                breakdown.storage += amount
            elif category == "Selling":
                breakdown.selling += amount
            elif category == "Waste":
                breakdown.waste += amount

        breakdown.total = (
            breakdown.acquisition
            + breakdown.transport
            + breakdown.processing
            + breakdown.storage
            + breakdown.selling
            + breakdown.waste
        )

        return breakdown

    def allocate_costs_to_assets(
        self,
        lot_id: int,
        method: str = "weight",
    ) -> list[ItemCost]:
        """
        Distribute a lot's total cost to individual assets.

        Methods:
        - 'weight': Allocate by weight (most common)
        - 'equal': Allocate equally regardless of size
        """
        lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            return []

        # Get all assets in this lot
        assets = (
            self.db.query(Asset)
            .join(Skid, Asset.skid_id == Skid.id)
            .filter(Skid.lot_id == lot_id)
            .all()
        )

        if not assets:
            return []

        # Get total cost
        total_cost = lot.acquisition_cost
        cost_breakdown = self.get_lot_cost_breakdown(lot_id)
        # Add processing and other allocated costs
        total_cost = cost_breakdown.total

        results = []
        total_weight = sum(a.weight_kg or Decimal("0") for a in assets) or Decimal("1")

        for asset in assets:
            if method == "weight":
                asset_weight = asset.weight_kg or Decimal("0")
                share = asset_weight / total_weight if total_weight > 0 else Decimal("0")
            else:  # equal
                share = Decimal("1") / len(assets)

            allocated = total_cost * share
            cost_per_kg = allocated / asset_weight if asset_weight and asset_weight > 0 else Decimal("0")

            results.append(ItemCost(
                asset_id=asset.id,
                asset_code=asset.asset_code,
                weight_kg=asset.weight_kg,
                allocated_cost=allocated,
                cost_per_kg=cost_per_kg,
                share_of_lot_pct=share * 100,
            ))

        return results

    def calculate_vegetable_profitability(
        self,
        vegetable_id: int,
        days: int = 180,
    ) -> VegetableProfitability:
        """Calculate profitability metrics for a vegetable type over time."""
        cutoff = datetime.now() - timedelta(days=days)

        # Get all lots of this vegetable
        lots = (
            self.db.query(Lot)
            .filter(
                Lot.vegetable_id == vegetable_id,
                Lot.acquired_at >= cutoff,
            )
            .all()
        )

        if not lots:
            veg = self.db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()
            return VegetableProfitability(
                vegetable_id=vegetable_id,
                vegetable_name=veg.name if veg else "Unknown",
                total_lots=0,
                total_kg_acquired=Decimal("0"),
                total_kg_sold=Decimal("0"),
                total_revenue=Decimal("0"),
                total_cost=Decimal("0"),
                gross_profit=Decimal("0"),
                profit_per_kg=Decimal("0"),
                margin_pct=Decimal("0"),
                waste_pct=Decimal("0"),
            )

        total_lots = len(lots)
        total_kg_acquired = sum(l.total_weight_kg for l in lots)

        # Get costs
        lot_ids = [l.id for l in lots]
        costs = self.db.query(CostEntry).filter(CostEntry.lot_id.in_(lot_ids)).all()
        total_cost = sum(c.amount or Decimal("0") for c in costs)

        # Get revenue from sales
        revenue_query = (
            self.db.query(func.coalesce(func.sum(SaleItem.line_total), 0))
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(
                SaleItem.vegetable_id == vegetable_id,
                Sale.sold_at >= cutoff,
                Sale.status == "Completed",
            )
            .scalar()
        )
        total_revenue = Decimal(str(revenue_query or 0))

        # Get kg sold
        sold_query = (
            self.db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(
                SaleItem.vegetable_id == vegetable_id,
                Sale.sold_at >= cutoff,
                Sale.status == "Completed",
            )
            .scalar()
        )
        total_kg_sold = Decimal(str(sold_query or 0))

        gross_profit = total_revenue - total_cost
        profit_per_kg = gross_profit / total_kg_sold if total_kg_sold > 0 else Decimal("0")
        margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        waste_pct = (
            ((total_kg_acquired - total_kg_sold) / total_kg_acquired * 100)
            if total_kg_acquired > 0
            else Decimal("0")
        )

        veg = self.db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()

        return VegetableProfitability(
            vegetable_id=vegetable_id,
            vegetable_name=veg.name if veg else "Unknown",
            total_lots=total_lots,
            total_kg_acquired=total_kg_acquired,
            total_kg_sold=total_kg_sold,
            total_revenue=total_revenue,
            total_cost=total_cost,
            gross_profit=gross_profit,
            profit_per_kg=profit_per_kg,
            margin_pct=margin_pct,
            waste_pct=waste_pct,
        )

    def calculate_waste_valuation(self, lot_id: int) -> WasteValuation:
        """Calculate the financial impact of waste for a lot."""
        from app.models.quality import SortResult

        lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            return None

        sort_result = (
            self.db.query(SortResult).filter(SortResult.lot_id == lot_id).first()
        )
        if not sort_result:
            return WasteValuation(
                lot_code=lot.lot_code,
                vegetable_name="Unknown",
                waste_kg=Decimal("0"),
                damaged_kg=Decimal("0"),
                recycle_kg=Decimal("0"),
                cost_of_waste=Decimal("0"),
                potential_revenue=Decimal("0"),
                net_loss=Decimal("0"),
            )

        waste_kg = (sort_result.damaged_kg or Decimal("0")) + (sort_result.recycle_kg or Decimal("0"))
        damaged_kg = sort_result.damaged_kg or Decimal("0")
        recycle_kg = sort_result.recycle_kg or Decimal("0")

        # Cost of waste = cost per kg * waste kg
        cost_breakdown = self.get_lot_cost_breakdown(lot_id)
        cost_per_kg = cost_breakdown.total / lot.total_weight_kg if lot.total_weight_kg > 0 else Decimal("0")
        cost_of_waste = cost_per_kg * waste_kg

        # Potential revenue = what we could have sold at Grade B price
        # (using grade B as a realistic price for damaged/recycled)
        veg = self.db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
        if veg and veg.category:
            from app.models.sales import Price
            grade_b = self.db.query(Grade).filter(Grade.code == "B").first()
            if grade_b:
                price = (
                    self.db.query(Price)
                    .filter(Price.vegetable_id == lot.vegetable_id, Price.grade_id == grade_b.id)
                    .first()
                )
                if price:
                    potential_revenue = (price.unit_price or Decimal("0")) * damaged_kg
                else:
                    potential_revenue = Decimal("0")
            else:
                potential_revenue = Decimal("0")
        else:
            potential_revenue = Decimal("0")

        # Recovery value for recycled items
        recovery_value = recycle_kg * Decimal("0.10")
        actual_revenue = potential_revenue + recovery_value

        net_loss = cost_of_waste - actual_revenue

        return WasteValuation(
            lot_code=lot.lot_code,
            vegetable_name=veg.name if veg else "Unknown",
            waste_kg=waste_kg,
            damaged_kg=damaged_kg,
            recycle_kg=recycle_kg,
            cost_of_waste=cost_of_waste,
            potential_revenue=potential_revenue,
            net_loss=net_loss,
        )

    def get_profitability_ranking(self, days: int = 180) -> list[VegetableProfitability]:
        """Rank all vegetables by profitability."""
        vegetables = self.db.query(Vegetable).all()
        rankings = []
        for veg in vegetables:
            prof = self.calculate_vegetable_profitability(veg.id, days=days)
            if prof.total_lots > 0:
                rankings.append(prof)
        # Sort by profit per kg descending
        rankings.sort(key=lambda r: r.profit_per_kg, reverse=True)
        return rankings
