"""
Sale Schemas
============
Sales transactions with line items.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Literal

from app.schemas.common import TimestampMixin, ImageInfo
from app.schemas.customer import CustomerListItem
from app.schemas.employee import EmployeeListItem
from app.schemas.vegetable import VegetableListItem
from app.schemas.grade import GradeRead


# ============================================
# STATUS OPTIONS
# ============================================

SaleStatus = Literal["Pending", "Completed", "Cancelled", "Refunded"]
PaymentMethod = Literal["cash", "card", "mobile", "credit", "check", "other"]


# ============================================
# SALE ITEM SCHEMAS
# ============================================

class SaleItemBase(BaseModel):
    """Shared sale item fields."""
    quantity: Decimal = Field(gt=Decimal("0"), le=Decimal("10000"))
    unit_type: str = Field(min_length=1, max_length=20)
    unit_price: Decimal = Field(ge=Decimal("0"), le=Decimal("10000"))
    line_total: Decimal = Field(ge=Decimal("0"), le=Decimal("100000"))
    notes: str | None = Field(default=None, max_length=500)


class SaleItemCreate(SaleItemBase):
    """Create a sale item."""
    inventory_id: int | None = Field(default=None, gt=0)
    asset_id: int | None = Field(default=None, gt=0)
    vegetable_id: int = Field(gt=0)
    grade_id: int = Field(gt=0)


class SaleItemRead(SaleItemBase):
    """Read a sale item with nested info."""
    id: int
    sale_id: int

    # Nested info
    vegetable: VegetableListItem | None = None
    grade: GradeRead | None = None

    model_config = {"from_attributes": True}


# ============================================
# SALE SCHEMAS
# ============================================

class SaleBase(BaseModel):
    """Shared sale fields."""
    sale_code: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^S-\d{4}-\d{5}$",
        description="Format: S-YYYY-NNNNN"
    )
    sold_at: datetime
    status: SaleStatus = Field(default="Completed")
    payment_method: PaymentMethod | None = None
    subtotal: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    tax: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    discount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    total_amount: Decimal = Field(ge=Decimal("0"))
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_amounts(self) -> "SaleBase":
        """Ensure subtotal + tax - discount = total_amount (within tolerance)."""
        expected = self.subtotal + self.tax - self.discount
        if abs(expected - self.total_amount) > Decimal("0.01"):
            raise ValueError(
                f"total_amount ({self.total_amount}) doesn't match "
                f"subtotal + tax - discount ({expected})"
            )
        if self.discount > self.subtotal:
            raise ValueError("Discount cannot exceed subtotal")
        return self


class SaleCreate(SaleBase):
    """Create a sale with line items."""
    customer_id: int | None = Field(default=None, gt=0)
    sold_by: int | None = Field(default=None, gt=0, description="Employee ID who recorded the sale")
    items: list[SaleItemCreate] = Field(min_length=1, description="At least one item required")


class SaleUpdate(BaseModel):
    """All fields optional for partial updates."""
    status: SaleStatus | None = Field(default=None)
    payment_method: PaymentMethod | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)


# ============================================
# READ — with nested relations
# ============================================

class SaleRead(SaleBase, TimestampMixin):
    """Full sale response with nested customer and items."""
    id: int

    # Nested objects
    customer: CustomerListItem | None = None
    sold_by_employee: EmployeeListItem | None = None
    items: list[SaleItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM — lightweight
# ============================================

class SaleListItem(BaseModel):
    """Minimal fields for list views."""
    id: int
    sale_code: str
    sold_at: datetime
    customer_id: int | None
    customer_name: str | None = None
    total_amount: Decimal
    payment_method: PaymentMethod | None
    status: SaleStatus
    item_count: int = Field(default=0, description="Number of line items")

    model_config = {"from_attributes": True}


# ============================================
# SALE SUMMARY — for reports
# ============================================

class SalesSummary(BaseModel):
    """Aggregated sales statistics for a period."""
    period_start: datetime
    period_end: datetime
    total_sales: int
    total_revenue: Decimal
    total_items_sold: int
    average_sale_value: Decimal
    top_customers: list[dict] = Field(default_factory=list)
    top_vegetables: list[dict] = Field(default_factory=list)
    payment_method_breakdown: dict[str, Decimal] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
