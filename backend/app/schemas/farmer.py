"""
Farmer Schemas
==============
Supplier entities with ratings, payment terms, and performance tracking.
"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, EmailStr

from app.schemas.common import ImageInfo, TimestampMixin


# ============================================
# BASE
# ============================================

class FarmerBase(BaseModel):
    """Shared farmer fields."""
    name: str = Field(min_length=2, max_length=120, description="Farm or business name")
    contact_person: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None, description="Validated email format")
    address: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=120, description="City/region")
    payment_terms: str | None = Field(
        default=None,
        max_length=60,
        description="e.g., 'Cash on Delivery', 'Net 7', 'Net 30'"
    )
    rating: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("5"),
        description="Quality rating 0.00 to 5.00"
    )
    is_active: bool = Field(default=True)
    notes: str | None = Field(default=None, max_length=1000)

    # Image support
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Strip non-digit characters for validation
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Phone number must have 7-15 digits")
        return v

    @field_validator("payment_terms")
    @classmethod
    def validate_payment_terms(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed_prefixes = ("Cash", "Net", "Due", "Prepaid", "COD")
        if not any(v.startswith(p) for p in allowed_prefixes):
            raise ValueError(f"Payment terms should start with one of: {', '.join(allowed_prefixes)}")
        return v


# ============================================
# CREATE
# ============================================

class FarmerCreate(FarmerBase):
    """All base fields available on creation."""
    pass


# ============================================
# UPDATE
# ============================================

class FarmerUpdate(BaseModel):
    """All fields optional for partial updates."""
    name: str | None = Field(default=None, min_length=2, max_length=120)
    contact_person: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=120)
    payment_terms: str | None = Field(default=None, max_length=60)
    rating: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("5"))
    is_active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)


# ============================================
# READ
# ============================================

class FarmerRead(FarmerBase, TimestampMixin):
    """Full farmer response with nested image."""
    id: int
    image: ImageInfo | None = None

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM (lightweight)
# ============================================

class FarmerListItem(BaseModel):
    """Minimal fields for list views."""
    id: int
    name: str
    location: str | None
    rating: Decimal | None
    is_active: bool
    payment_terms: str | None
    image_url: str | None = None

    model_config = {"from_attributes": True}


# ============================================
# PERFORMANCE METRICS (computed)
# ============================================

class FarmerPerformance(BaseModel):
    """Computed metrics for a farmer."""
    farmer_id: int
    farmer_name: str
    total_lots: int = Field(description="Number of lots supplied")
    total_purchase_value: Decimal = Field(description="Total $ purchased")
    average_grade_distribution: dict[str, int] = Field(
        description="Count of grades in their lots (e.g., {'A': 5, 'B': 10})"
    )
    on_time_delivery_rate: float = Field(
        ge=0, le=1,
        description="Fraction of POs delivered on or before expected date"
    )
    fill_rate: float = Field(
        ge=0, le=1,
        description="Fraction of expected quantity delivered"
    )

    model_config = {"from_attributes": True}
