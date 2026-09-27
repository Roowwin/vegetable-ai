"""
Lot Schemas
===========
The central entity. Lots track vegetables from acquisition to sale.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Literal

from app.schemas.common import TimestampMixin, ImageInfo
from app.schemas.vegetable import VegetableListItem
from app.schemas.farmer import FarmerListItem
from app.schemas.grade import GradeRead


# ============================================
# STATUS OPTIONS
# ============================================

LotStatus = Literal[
    "Registered",
    "Skidded",
    "Sorted",
    "Tested",
    "Graded",
    "InInventory",
    "OnSale",
    "PartiallySold",
    "FullySold",
    "Discounted",
    "Closed",
    "Recycled",
]

SourceType = Literal["collection_trip", "delivery", "market", "other"]


# ============================================
# BASE
# ============================================

class LotBase(BaseModel):
    """Shared lot fields."""
    lot_code: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^L-\d{4}-\d{5}$",
        description="Format: L-YYYY-NNNNN (e.g., L-2024-00001)"
    )
    acquired_at: datetime
    total_weight_kg: Decimal = Field(ge=Decimal("0"), le=Decimal("100000"))
    acquisition_cost: Decimal = Field(ge=Decimal("0"), le=Decimal("1000000"))
    status: LotStatus = Field(default="Registered")
    source_type: SourceType = Field(default="purchase_order")
    notes: str | None = Field(default=None, max_length=1000)


# ============================================
# CREATE
# ============================================

class LotCreate(LotBase):
    """Create a new lot. Requires foreign keys."""
    vegetable_id: int = Field(gt=0)
    purchase_order_id: int | None = Field(default=None, gt=0)
    source_id: int | None = Field(default=None, gt=0)


# ============================================
# UPDATE
# ============================================

class LotUpdate(BaseModel):
    """All fields optional for partial updates."""
    status: LotStatus | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)


# ============================================
# READ — with nested relations
# ============================================

class LotRead(LotBase, TimestampMixin):
    """Full lot response with nested farmer and vegetable."""
    id: int

    # Nested objects (resolved by the service layer)
    vegetable: VegetableListItem | None = None
    farmer: FarmerListItem | None = None
    grade: GradeRead | None = Field(default=None, description="Dominant grade if tested")

    # Nested image (for visual identification)
    image: ImageInfo | None = None

    # Computed fields
    total_revenue: Decimal | None = Field(default=None, description="Sum of all sales for this lot")
    remaining_weight_kg: Decimal | None = Field(default=None, description="Unsold weight")

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM — lightweight
# ============================================

class LotListItem(BaseModel):
    """Minimal fields for list views."""
    id: int
    lot_code: str
    vegetable_id: int
    vegetable_name: str | None = None
    farmer_id: int | None = None
    farmer_name: str | None = None
    acquired_at: datetime
    total_weight_kg: Decimal
    acquisition_cost: Decimal
    status: LotStatus
    image_url: str | None = None

    model_config = {"from_attributes": True}


# ============================================
# PROFIT & LOSS — detailed breakdown
# ============================================

class CostBreakdown(BaseModel):
    """Costs broken down by category."""
    acquisition: Decimal = Field(default=Decimal("0"))
    transport: Decimal = Field(default=Decimal("0"))
    processing: Decimal = Field(default=Decimal("0"))
    storage: Decimal = Field(default=Decimal("0"))
    selling: Decimal = Field(default=Decimal("0"))
    waste: Decimal = Field(default=Decimal("0"))
    total: Decimal = Field(default=Decimal("0"))

    model_config = {"from_attributes": True}


class LotProfitLoss(BaseModel):
    """
    Detailed P&L breakdown for a single lot.
    This is the KEY business query: "How much money did Lot L001 really make?"
    """
    lot_code: str
    vegetable_name: str
    farmer_name: str

    # Costs
    total_cost: CostBreakdown
    cost_per_kg: Decimal

    # Revenue
    total_revenue: Decimal = Decimal("0")
    revenue_per_kg: Decimal = Decimal("0")
    sold_weight_kg: Decimal = Decimal("0")

    # Waste
    waste_kg: Decimal = Decimal("0")
    waste_pct: Decimal = Decimal("0")
    waste_recovery_value: Decimal = Decimal("0")

    # Profit
    gross_profit: Decimal = Decimal("0")
    gross_margin_pct: Decimal = Decimal("0")
    net_profit: Decimal = Decimal("0")
    net_margin_pct: Decimal = Decimal("0")
    profit_per_kg: Decimal = Decimal("0")

    # Metadata
    status: LotStatus
    acquired_at: datetime
    closed_at: datetime | None = None

    model_config = {"from_attributes": True}
