"""
Employee Schemas
================
Staff entities (owner, driver, sorter, cashier).
"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Literal

from app.schemas.common import ImageInfo, TimestampMixin


# ============================================
# BASE
# ============================================

EmployeeRole = Literal["owner", "driver", "sorter", "cashier", "helper", "manager"]


class EmployeeBase(BaseModel):
    """Shared employee fields."""
    name: str = Field(min_length=2, max_length=120)
    role: EmployeeRole = Field(description="Job role in the shop")
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None)
    hourly_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1000"),
        description="Hourly wage (0-1000)"
    )
    hire_date: date | None = Field(default=None)
    is_active: bool = Field(default=True)
    notes: str | None = Field(default=None, max_length=1000)

    # Image (profile photo)
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

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, v: Decimal | None) -> Decimal | None:
        # Owner has no hourly rate (gets paid differently)
        return v


# ============================================
# CREATE
# ============================================

class EmployeeCreate(EmployeeBase):
    pass


# ============================================
# UPDATE
# ============================================

class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: EmployeeRole | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = Field(default=None)
    hourly_rate: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1000"))
    hire_date: date | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt_text: str | None = Field(default=None, max_length=200)


# ============================================
# READ
# ============================================

class EmployeeRead(EmployeeBase, TimestampMixin):
    id: int
    image: ImageInfo | None = None

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM
# ============================================

class EmployeeListItem(BaseModel):
    id: int
    name: str
    role: EmployeeRole
    is_active: bool
    image_url: str | None

    model_config = {"from_attributes": True}
