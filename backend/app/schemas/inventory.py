"""
Inventory Schemas
=================
Current stock of vegetables available for sale.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Literal

from app.schemas.common import TimestampMixin, ImageInfo
from app.schemas.vegetable import VegetableListItem
from app.schemas.grade import GradeRead


# ============================================
# STATUS OPTIONS
# ============================================

InventoryTxnType = Literal["Received", "Sold", "Adjustment", "Transfer", "Returned"]


# ============================================
# INVENTORY ITEM SCHEMAS
# ============================================

class InventoryBase(BaseModel):
    """Shared inventory fields."""
    location: str = Field(default="Main Shop", min_length=1, max_length=60)
    quantity_kg: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100000"))
    quantity_units: int | None = Field(default=None, ge=0, le=100000)
    available_from: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_available: bool = Field(default=True)

    @field_validator("expires_at")
    @classmethod
    def validate_expiry_after_available(cls, v: datetime | None, info) -> datetime | None:
        if v is None:
            return v
        available_from = info.data.get("available_from")
        if available_from and v <= available_from:
            raise ValueError("expires_at must be after available_from")
        return v


class InventoryCreate(InventoryBase):
    """Create inventory entry."""
    asset_id: int | None = Field(default=None, gt=0)


class InventoryUpdate(BaseModel):
    """All fields optional for partial updates."""
    location: str | None = Field(default=None, min_length=1, max_length=60)
    quantity_kg: Decimal | None = Field(default=None, ge=Decimal("0"))
    quantity_units: int | None = Field(default=None, ge=0)
    available_from: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_available: bool | None = Field(default=None)


class InventoryRead(InventoryBase, TimestampMixin):
    """Full inventory response."""
    id: int
    asset_id: int | None = None

    # Nested info
    vegetable: VegetableListItem | None = None
    grade: GradeRead | None = None

    # Computed
    days_until_expiry: int | None = Field(default=None, description="Negative if expired")
    is_expiring_soon: bool = Field(default=False, description="True if expires within 2 days")

    model_config = {"from_attributes": True}


class InventoryListItem(BaseModel):
    """Lightweight for list views."""
    id: int
    location: str
    quantity_kg: Decimal | None
    quantity_units: int | None
    is_available: bool
    vegetable_name: str | None = None
    grade_code: str | None = None
    image_url: str | None = None
    expires_at: datetime | None = None
    days_until_expiry: int | None = None

    model_config = {"from_attributes": True}


# ============================================
# INVENTORY TRANSACTION SCHEMAS
# ============================================

class InventoryTransactionBase(BaseModel):
    txn_type: InventoryTxnType
    qty_change_kg: Decimal | None = Field(default=None, ge=Decimal("-100000"), le=Decimal("100000"))
    qty_change_units: int | None = Field(default=None, ge=-100000, le=100000)
    reference_type: str | None = Field(default=None, max_length=32)
    reference_id: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)


class InventoryTransactionCreate(InventoryTransactionBase):
    inventory_id: int = Field(gt=0)


class InventoryTransactionRead(InventoryTransactionBase, TimestampMixin):
    id: int
    inventory_id: int
    created_by: int | None = None

    model_config = {"from_attributes": True}


class InventoryTransactionListItem(BaseModel):
    """Minimal transaction for audit views."""
    id: int
    inventory_id: int
    txn_type: InventoryTxnType
    qty_change_kg: Decimal | None
    qty_change_units: int | None
    created_at: datetime
    reference_type: str | None
    notes: str | None

    model_config = {"from_attributes": True}
