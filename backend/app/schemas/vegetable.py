"""
Vegetable Schemas
=================
With image support for product catalog display.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ImageInfo, TimestampMixin


# ============================================
# BASE
# ============================================

class VegetableBase(BaseModel):
    """Shared fields for all vegetable schemas."""
    name: str = Field(min_length=2, max_length=80, description="Display name (e.g., 'Tomato')")
    category: str | None = Field(
        default=None,
        max_length=40,
        description="Category: leafy, root, fruit, legume, cruciferous"
    )
    default_unit_type: str = Field(default="kg", max_length=20)
    shelf_life_days: int | None = Field(default=None, ge=1, le=365)
    typical_waste_pct: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("100"),
        description="Expected waste percentage (0-100)"
    )
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=1000)

    # Image support ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â single primary image
    image_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to vegetable image (Unsplash, CDN, etc.)"
    )
    image_alt_text: str | None = Field(
        default=None,
        max_length=200,
        description="Alt text for accessibility"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"leafy", "root", "fruit", "legume", "cruciferous", "herb", "mushroom"}
        if v.lower() not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("default_unit_type")
    @classmethod
    def validate_unit_type(cls, v: str) -> str:
        allowed = {"kg", "piece", "half", "quarter", "bunch", "crate", "custom"}
        if v.lower() not in allowed:
            raise ValueError(f"Unit type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


# ============================================
# CREATE
# ============================================

class VegetableCreate(VegetableBase):
    """Required to create a vegetable. All base fields are required."""
    pass


# ============================================
# UPDATE (PATCH semantics ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â all fields optional)
# ============================================

class VegetableUpdate(BaseModel):
    """All fields optional for partial updates."""
    name: str | None = Field(default=None, min_length=2, max_length=80)
    category: str | None = Field(default=None, max_length=40)
    default_unit_type: str | None = Field(default=None, max_length=20)
    shelf_life_days: int | None = Field(default=None, ge=1, le=365)
    typical_waste_pct: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"leafy", "root", "fruit", "legume", "cruciferous", "herb", "mushroom"}
        if v.lower() not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


# ============================================
# READ (Response)
# ============================================

class VegetableRead(VegetableBase, TimestampMixin):
    """Returned in API responses."""
    id: int

    # Nested image info (built from image_url + image_alt_text)
    image: ImageInfo | None = Field(default=None, description="Image info if available")

    model_config = {"from_attributes": True}


# ============================================
# LIST RESPONSE
# ============================================

class VegetableListItem(BaseModel):
    """Lightweight representation for list endpoints."""
    id: int
    name: str
    category: str | None
    default_unit_type: str
    image_url: str | None = None
    image_alt_text: str | None = None

    model_config = {"from_attributes": True}
