"""
Purchase Order Schemas
======================
Procurement from farmers.
"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Literal

from app.schemas.common import TimestampMixin
from app.schemas.farmer import FarmerListItem
from app.schemas.vegetable import VegetableListItem


# ============================================
# STATUS OPTIONS
# ============================================

POStatus = Literal[
    "Draft",
    "Issued",
    "Acknowledged",
    "PartiallyReceived",
    "FullyReceived",
    "Closed",
    "Cancelled",
]

DeliveryMode = Literal["Collection", "FarmerDelivery"]


# ============================================
# PO ITEM SCHEMAS
# ============================================

class POItemBase(BaseModel):
    expected_quantity_kg: Decimal = Field(gt=Decimal("0"), le=Decimal("100000"))
    expected_unit_price: Decimal = Field(ge=Decimal("0"), le=Decimal("10000"))
    expected_total: Decimal = Field(ge=Decimal("0"), le=Decimal("1000000"))
    received_quantity_kg: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    actual_unit_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_received_not_exceed_expected(self) -> "POItemBase":
        if self.received_quantity_kg > self.expected_quantity_kg:
            raise ValueError("received_quantity_kg cannot exceed expected_quantity_kg")
        return self


class POItemCreate(POItemBase):
    vegetable_id: int = Field(gt=0)


class POItemRead(POItemBase):
    id: int
    purchase_order_id: int
    vegetable: VegetableListItem | None = None

    # Computed
    variance_kg: Decimal = Field(default=Decimal("0"), description="received - expected")
    variance_pct: Decimal = Field(default=Decimal("0"))
    fill_rate: Decimal = Field(default=Decimal("0"), description="received / expected")

    model_config = {"from_attributes": True}


# ============================================
# PURCHASE ORDER SCHEMAS
# ============================================

class PurchaseOrderBase(BaseModel):
    po_number: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^PO-\d{4}-\d{5}$",
        description="Format: PO-YYYY-NNNNN"
    )
    status: POStatus = Field(default="Draft")
    issue_date: date
    expected_delivery_date: date | None = Field(default=None)
    actual_delivery_date: date | None = Field(default=None)
    total_expected_value: Decimal = Field(ge=Decimal("0"))
    total_actual_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    payment_terms: str | None = Field(default=None, max_length=64)
    delivery_mode: DeliveryMode
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_delivery_dates(self) -> "PurchaseOrderBase":
        if (
            self.expected_delivery_date
            and self.actual_delivery_date
            and self.actual_delivery_date < self.issue_date
        ):
            raise ValueError("actual_delivery_date cannot be before issue_date")
        return self


class PurchaseOrderCreate(PurchaseOrderBase):
    farmer_id: int = Field(gt=0)
    created_by: int | None = Field(default=None, gt=0)
    items: list[POItemCreate] = Field(min_length=1, description="At least one item")


class PurchaseOrderUpdate(BaseModel):
    status: POStatus | None = Field(default=None)
    expected_delivery_date: date | None = Field(default=None)
    actual_delivery_date: date | None = Field(default=None)
    total_actual_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    notes: str | None = Field(default=None, max_length=1000)


class PurchaseOrderRead(PurchaseOrderBase, TimestampMixin):
    id: int
    farmer_id: int
    farmer: FarmerListItem | None = None
    created_by: int | None = None
    items: list[POItemRead] = Field(default_factory=list)

    # Computed
    fill_rate: Decimal = Field(default=Decimal("0"), description="Total received / total expected")
    is_overdue: bool = Field(default=False, description="Past expected delivery and not fully received")

    model_config = {"from_attributes": True}


class PurchaseOrderListItem(BaseModel):
    """Minimal fields for list views."""
    id: int
    po_number: str
    farmer_name: str | None = None
    status: POStatus
    issue_date: date
    expected_delivery_date: date | None
    actual_delivery_date: date | None
    total_expected_value: Decimal
    total_actual_value: Decimal | None
    item_count: int = Field(default=0)
    delivery_mode: DeliveryMode
    is_overdue: bool = False

    model_config = {"from_attributes": True}
