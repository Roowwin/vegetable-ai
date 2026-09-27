"""
Dashboard Schemas
=================
KPI responses for the analytics dashboard.
"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.common import TimestampMixin


# ============================================
# KPI CARDS
# ============================================

class KPISummary(BaseModel):
    """Top-level KPI cards for dashboard hero section."""
    # Counts
    active_lots: int = Field(description="Lots currently in inventory or being processed")
    total_lots: int = Field(description="All-time lot count")
    open_purchase_orders: int = Field(description="POs not yet fully received")
    overdue_purchase_orders: int = Field(description="POs past expected delivery")

    # Financial
    total_revenue_mtd: Decimal = Field(description="Month-to-date revenue")
    total_profit_mtd: Decimal = Field(description="Month-to-date net profit")
    profit_margin_mtd: Decimal = Field(description="Profit margin % (0-100)")

    # Quality
    average_grade_score: Decimal = Field(description="Weighted avg grade score (A=1, RECYCLE=7)")
    waste_percentage_mtd: Decimal = Field(description="MTD waste %")

    # Inventory
    inventory_value: Decimal = Field(description="Current inventory value at cost")
    low_stock_items: int = Field(description="Items with < 7 days until expiry")

    # Period
    period_start: date
    period_end: date

    model_config = {"from_attributes": True}


# ============================================
# TIME SERIES DATA
# ============================================

class TimeSeriesPoint(BaseModel):
    """Single data point in a time series."""
    date: date
    value: Decimal
    label: str | None = Field(default=None, description="Optional label")

    model_config = {"from_attributes": True}


class RevenueTimeSeries(BaseModel):
    """Revenue trend over time."""
    period: Literal["daily", "weekly", "monthly"]
    data: list[TimeSeriesPoint]

    model_config = {"from_attributes": True}


class SalesVolumeTimeSeries(BaseModel):
    """Sales volume (kg) over time per vegetable or grade."""
    period: Literal["daily", "weekly", "monthly"]
    series: dict[str, list[TimeSeriesPoint]] = Field(
        description="Keyed by vegetable name or grade code"
    )

    model_config = {"from_attributes": True}


# ============================================
# BREAKDOWN / DISTRIBUTION
# ============================================

class GradeDistribution(BaseModel):
    """Distribution of items across grade codes."""
    grade_code: str
    grade_name: str
    count: int
    percentage: Decimal = Field(description="Percentage of total (0-100)")

    model_config = {"from_attributes": True}


class VegetableBreakdown(BaseModel):
    """Sales/profit breakdown by vegetable."""
    vegetable_id: int
    vegetable_name: str
    vegetable_image: str | None = None
    total_kg_sold: Decimal
    total_revenue: Decimal
    total_profit: Decimal
    profit_margin: Decimal

    model_config = {"from_attributes": True}


class SupplierPerformance(BaseModel):
    """Performance comparison across farmers."""
    farmer_id: int
    farmer_name: str
    total_lots: int
    total_value: Decimal
    on_time_delivery_rate: Decimal = Field(ge=0, le=1)
    average_grade: Decimal
    quality_score: Decimal = Field(ge=0, le=10, description="0-10 quality rating")

    model_config = {"from_attributes": True}


# ============================================
# DASHBOARD ALERTS (defined BEFORE DashboardData)
# ============================================

class DashboardAlert(BaseModel):
    """Alerts shown to the owner (low stock, overdue POs, anomalies)."""
    severity: Literal["info", "warning", "critical"]
    category: Literal["inventory", "purchase", "quality", "financial"]
    title: str
    message: str
    action_url: str | None = Field(default=None, description="Where to go to resolve")
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# DASHBOARD FULL RESPONSE
# ============================================

class DashboardData(BaseModel):
    """Complete dashboard response - all the pieces the frontend needs."""
    kpis: KPISummary
    revenue_trend: RevenueTimeSeries
    sales_by_vegetable: list[VegetableBreakdown]
    grade_distribution: list[GradeDistribution]
    top_suppliers: list[SupplierPerformance]
    alerts: list[DashboardAlert]

    model_config = {"from_attributes": True}


# ============================================
# FORECAST SCHEMAS (preview for Milestone 11)
# ============================================

class ForecastPoint(BaseModel):
    """Single forecast data point."""
    date: date
    predicted_value: Decimal
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    """Forecast query response."""
    target: Literal["sales_volume", "revenue", "profit", "demand", "waste"]
    vegetable_id: int | None = None
    grade_id: int | None = None
    model_name: str
    predictions: list[ForecastPoint]
    generated_at: datetime

    model_config = {"from_attributes": True}
