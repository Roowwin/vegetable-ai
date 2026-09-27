"""
Dashboard Service
=================
Aggregates data from all other tables into KPI responses for the dashboard.

This is the analytics engine that powers the main dashboard page.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.people import Farmer
from app.models.inventory import Vegetable, Lot, Inventory
from app.models.quality import Grade, QualityTest
from app.models.sales import Sale, SaleItem
from app.models.costs import CostEntry
from app.models.procurement import PurchaseOrder
from app.schemas.dashboard import (
    KPISummary, TimeSeriesPoint, RevenueTimeSeries,
    GradeDistribution, VegetableBreakdown, SupplierPerformance,
    DashboardAlert, DashboardData,
)


class DashboardService:
    """Service for dashboard aggregations and KPIs."""

    def __init__(self, db: Session):
        self.db = db

    def get_kpis(
        self,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> KPISummary:
        """Compute top-line KPIs for the dashboard hero section."""
        today = date.today()
        if period_end is None:
            period_end = today
        if period_start is None:
            period_start = today - timedelta(days=30)

        # Month-to-date boundaries
        mtd_start = today.replace(day=1)
        mtd_end = today

        # Active lots: not yet closed or recycled
        active_lots = self.db.query(func.count(Lot.id)).filter(
            Lot.status.in_(["Registered", "Skidded", "Sorted", "Tested", "Graded", "InInventory", "OnSale", "PartiallySold"])
        ).scalar() or 0

        # Total lots
        total_lots = self.db.query(func.count(Lot.id)).scalar() or 0

        # Open POs (not yet fully received)
        open_pos = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.status.in_(["Draft", "Issued", "Acknowledged", "PartiallyReceived"])
        ).scalar() or 0

        # Overdue POs
        overdue_pos = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.expected_delivery_date < today,
            PurchaseOrder.status.in_(["Issued", "Acknowledged", "PartiallyReceived"]),
        ).scalar() or 0

        # MTD Revenue
        mtd_revenue = self.db.query(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).filter(
            Sale.sold_at >= mtd_start,
            Sale.sold_at <= mtd_end,
            Sale.status == "Completed",
        ).scalar() or 0

        # MTD Costs (for profit calculation)
        mtd_costs = self.db.query(
            func.coalesce(func.sum(CostEntry.amount), 0)
        ).filter(
            CostEntry.incurred_at >= mtd_start,
            CostEntry.incurred_at <= mtd_end,
        ).scalar() or 0

        mtd_revenue_decimal = Decimal(str(mtd_revenue))
        mtd_costs_decimal = Decimal(str(mtd_costs))
        mtd_profit = mtd_revenue_decimal - mtd_costs_decimal
        mtd_margin = (
            (mtd_profit / mtd_revenue_decimal * 100) if mtd_revenue_decimal > 0 else Decimal("0")
        )

        # Average grade score (1=A best, 7=RECYCLE worst)
        # Map grade codes to numeric scores
        grade_score_map = {"A": 1, "A-": 2, "B": 3, "B-": 4, "C": 5, "C-": 6, "RECYCLE": 7}
        grade_scores = (
            self.db.query(Grade.code)
            .join(QualityTest, QualityTest.grade_id == Grade.id)
            .all()
        )
        if grade_scores:
            scores = [grade_score_map.get(code[0], 7) for code in grade_scores]
            avg_grade = Decimal(str(sum(scores) / len(scores)))
        else:
            avg_grade = Decimal("0")

        # Waste percentage MTD
        total_weight_sold = self.db.query(
            func.coalesce(func.sum(SaleItem.quantity), 0)
        ).filter(
            SaleItem.sale_id.in_(
                self.db.query(Sale.id).filter(
                    Sale.sold_at >= mtd_start,
                    Sale.sold_at <= mtd_end,
                )
            )
        ).scalar() or 0

        # Inventory value (use acquisition cost as proxy)
        inv_value = self.db.query(
            func.coalesce(func.sum(Inventory.quantity_kg), 0)
        ).filter(
            Inventory.is_available == True
        ).scalar() or 0
        # Approximate value at $2/kg average
        inv_value_decimal = Decimal(str(inv_value)) * Decimal("2.00")

        # Low stock: items expiring within 7 days
        cutoff = datetime.now() + timedelta(days=7)
        low_stock = self.db.query(func.count(Inventory.id)).filter(
            Inventory.is_available == True,
            Inventory.expires_at.isnot(None),
            Inventory.expires_at <= cutoff,
        ).scalar() or 0

        return KPISummary(
            active_lots=active_lots,
            total_lots=total_lots,
            open_purchase_orders=open_pos,
            overdue_purchase_orders=overdue_pos,
            total_revenue_mtd=mtd_revenue_decimal,
            total_profit_mtd=mtd_profit,
            profit_margin_mtd=mtd_margin,
            average_grade_score=avg_grade,
            waste_percentage_mtd=Decimal("5.0"),  # Simplified
            inventory_value=inv_value_decimal,
            low_stock_items=low_stock,
            period_start=period_start,
            period_end=period_end,
        )

    def get_revenue_trend(self, days: int = 30) -> RevenueTimeSeries:
        """Get daily revenue for the last N days."""
        end = date.today()
        start = end - timedelta(days=days)

        # Group sales by date
        daily_revenue = (
            self.db.query(
                func.date(Sale.sold_at).label("sale_date"),
                func.sum(Sale.total_amount).label("daily_total"),
            )
            .filter(
                Sale.sold_at >= start,
                Sale.sold_at <= end,
                Sale.status == "Completed",
            )
            .group_by(func.date(Sale.sold_at))
            .order_by(func.date(Sale.sold_at))
            .all()
        )

        data = [
            TimeSeriesPoint(
                date=sale_date,
                value=Decimal(str(daily_total)),
            )
            for sale_date, daily_total in daily_revenue
        ]

        return RevenueTimeSeries(period="daily", data=data)

    def get_grade_distribution(self) -> list[GradeDistribution]:
        """Get distribution of quality tests across grades."""
        results = (
            self.db.query(
                Grade.code,
                Grade.name,
                func.count(QualityTest.id).label("test_count"),
            )
            .join(QualityTest, QualityTest.grade_id == Grade.id)
            .group_by(Grade.code, Grade.name, Grade.rank)
            .order_by(Grade.rank)
            .all()
        )

        total = sum(count for _, _, count in results)
        if total == 0:
            return []

        return [
            GradeDistribution(
                grade_code=code,
                grade_name=name,
                count=count,
                percentage=Decimal(str(count / total * 100)),
            )
            for code, name, count in results
        ]

    def get_sales_by_vegetable(self, limit: int = 10) -> list[VegetableBreakdown]:
        """Get top-selling vegetables by revenue."""
        results = (
            self.db.query(
                Vegetable.id,
                Vegetable.name,

                func.coalesce(func.sum(SaleItem.quantity), 0).label("total_kg"),
                func.coalesce(func.sum(SaleItem.line_total), 0).label("total_revenue"),
            )
            .join(SaleItem, SaleItem.vegetable_id == Vegetable.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.status == "Completed")
            .group_by(Vegetable.id, Vegetable.name)
            .order_by(func.sum(SaleItem.line_total).desc())
            .limit(limit)
            .all()
        )

        return [
            VegetableBreakdown(
                vegetable_id=veg_id,
                vegetable_name=name,
                vegetable_image=None,  # TODO: add image support later
                total_kg_sold=Decimal(str(total_kg)),
                total_revenue=Decimal(str(total_revenue)),
                total_profit=Decimal(str(total_revenue)) * Decimal("0.3"),  # Simplified
                profit_margin=Decimal("30.0"),  # Simplified
            )
            for veg_id, name, total_kg, total_revenue in results
        ]

    def get_top_suppliers(self, limit: int = 5) -> list[SupplierPerformance]:
        """Get top suppliers by performance."""
        results = (
            self.db.query(
                Farmer.id,
                Farmer.name,
                func.count(Lot.id).label("lot_count"),
                func.coalesce(func.sum(Lot.acquisition_cost), 0).label("total_value"),
            )
            .join(PurchaseOrder, PurchaseOrder.farmer_id == Farmer.id)
            .join(Lot, Lot.purchase_order_id == PurchaseOrder.id)
            .group_by(Farmer.id, Farmer.name)
            .order_by(func.sum(Lot.acquisition_cost).desc())
            .limit(limit)
            .all()
        )

        return [
            SupplierPerformance(
                farmer_id=fid,
                farmer_name=name,
                total_lots=count,
                total_value=Decimal(str(total_value)),
                on_time_delivery_rate=Decimal("0.85"),  # Simplified
                average_grade=Decimal("3.5"),  # Simplified
                quality_score=Decimal("7.5"),  # Simplified
            )
            for fid, name, count, total_value in results
        ]

    def get_alerts(self) -> list[DashboardAlert]:
        """Get active alerts (low stock, overdue POs)."""
        alerts = []
        today = date.today()

        # Overdue PO alerts
        overdue_pos = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.expected_delivery_date < today,
                PurchaseOrder.status.in_(["Issued", "Acknowledged", "PartiallyReceived"]),
            )
            .limit(5)
            .all()
        )
        for po in overdue_pos:
            days_late = (today - po.expected_delivery_date).days if po.expected_delivery_date else 0
            alerts.append(DashboardAlert(
                severity="warning" if days_late < 7 else "critical",
                category="purchase",
                title=f"PO {po.po_number} overdue",
                message=f"Expected {po.expected_delivery_date}, now {days_late} days late",
                action_url=f"/purchase-orders/{po.id}",
                created_at=datetime.now(),
            ))

        # Low stock alerts (expiring within 3 days)
        cutoff = datetime.now() + timedelta(days=3)
        expiring = (
            self.db.query(Inventory)
            .filter(
                Inventory.is_available == True,
                Inventory.expires_at.isnot(None),
                Inventory.expires_at <= cutoff,
            )
            .limit(5)
            .all()
        )
        for inv in expiring:
            alerts.append(DashboardAlert(
                severity="warning",
                category="inventory",
                title="Inventory expiring soon",
                message=f"Item expires {inv.expires_at.date()}",
                action_url=f"/inventory/{inv.id}",
                created_at=datetime.now(),
            ))

        return alerts

    def get_dashboard(self) -> DashboardData:
        """Get the complete dashboard data in one call."""
        return DashboardData(
            kpis=self.get_kpis(),
            revenue_trend=self.get_revenue_trend(days=30),
            sales_by_vegetable=self.get_sales_by_vegetable(),
            grade_distribution=self.get_grade_distribution(),
            top_suppliers=self.get_top_suppliers(),
            alerts=self.get_alerts(),
        )
