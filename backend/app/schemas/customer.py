"""
Customer Schemas
================
Buyer entities (individuals and businesses).
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Literal

from app.schemas.common import ImageInfo, TimestampMixin


# ============================================
# BASE
# ============================================

CustomerType = Literal["individual", "business"]


class CustomerBase(BaseModel):
    """Shared customer fields."""
    name: str = Field(min_length=2, max_length=120)
    customer_type: CustomerType = Field(default="individual")
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    notes: str | None = Field(default=None, max_length=1000)

    # Image (e.g., business logo for business customers)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Phone number must have 7-15 digits")
        return v


# ============================================
# CREATE
# ============================================

class CustomerCreate(CustomerBase):
    pass


# ============================================
# UPDATE
# ============================================

class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    customer_type: CustomerType | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    is_active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)


# ============================================
# READ
# ============================================

class CustomerRead(CustomerBase, TimestampMixin):
    id: int
    image: ImageInfo | None = None

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM
# ============================================

class CustomerListItem(BaseModel):
    id: int
    name: str
    customer_type: CustomerType
    is_active: bool
    image_url: str | None

    model_config = {"from_attributes": True}


# ============================================
# CUSTOMER ANALYTICS (computed)
# ============================================

class CustomerStats(BaseModel):
    """Computed statistics for a customer."""
    customer_id: int
    customer_name: str
    total_purchases: int
    total_spent: Decimal
    average_order_value: Decimal
    first_purchase_date: datetime | None
    last_purchase_date: datetime | None
    favorite_vegetables: list[str] = Field(
        default_factory=list,
        description="Top 3 most-purchased vegetables"
    )

    model_config = {"from_attributes": True}
