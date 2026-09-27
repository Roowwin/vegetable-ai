"""
Dashboard Endpoint
==================
Single endpoint that powers the main dashboard page.
"""

from fastapi import APIRouter, Depends
from typing import Annotated

from app.api.deps import DbSession, PaginationParams
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", summary="Get complete dashboard data")
async def get_dashboard(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
):
    """Get the complete dashboard data: KPIs, charts, alerts."""
    service = DashboardService(db)
    dashboard = service.get_dashboard()
    return {
        "kpis": {
            "active_lots": dashboard.kpis.active_lots,
            "total_lots": dashboard.kpis.total_lots,
            "open_purchase_orders": dashboard.kpis.open_purchase_orders,
            "overdue_purchase_orders": dashboard.kpis.overdue_purchase_orders,
            "total_revenue_mtd": float(dashboard.kpis.total_revenue_mtd),
            "total_profit_mtd": float(dashboard.kpis.total_profit_mtd),
            "profit_margin_mtd": float(dashboard.kpis.profit_margin_mtd),
            "average_grade_score": float(dashboard.kpis.average_grade_score),
            "waste_percentage_mtd": float(dashboard.kpis.waste_percentage_mtd),
            "inventory_value": float(dashboard.kpis.inventory_value),
            "low_stock_items": dashboard.kpis.low_stock_items,
            "period_start": dashboard.kpis.period_start.isoformat(),
            "period_end": dashboard.kpis.period_end.isoformat(),
        },
        "revenue_trend": {
            "period": dashboard.revenue_trend.period,
            "data": [{"date": p.date.isoformat(), "value": float(p.value)} for p in dashboard.revenue_trend.data],
        },
        "sales_by_vegetable": [
            {
                "vegetable_id": v.vegetable_id,
                "vegetable_name": v.vegetable_name,
                "total_kg_sold": float(v.total_kg_sold),
                "total_revenue": float(v.total_revenue),
                "total_profit": float(v.total_profit),
                "profit_margin": float(v.profit_margin),
            }
            for v in dashboard.sales_by_vegetable
        ],
        "grade_distribution": [
            {
                "grade_code": g.grade_code,
                "grade_name": g.grade_name,
                "count": g.count,
                "percentage": float(g.percentage),
            }
            for g in dashboard.grade_distribution
        ],
        "top_suppliers": [
            {
                "farmer_id": s.farmer_id,
                "farmer_name": s.farmer_name,
                "total_lots": s.total_lots,
                "total_value": float(s.total_value),
            }
            for s in dashboard.top_suppliers
        ],
        "alerts": [
            {
                "severity": a.severity,
                "category": a.category,
                "title": a.title,
                "message": a.message,
                "created_at": a.created_at.isoformat(),
            }
            for a in dashboard.alerts
        ],
    }
