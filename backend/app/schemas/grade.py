"""
Grade Schemas
=============
Quality grade hierarchy (A, A-, B, B-, C, C-, RECYCLE).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal

from app.schemas.common import TimestampMixin


# ============================================
# CONSTANTS
# ============================================

GradeCode = Literal["A", "A-", "B", "B-", "C", "C-", "RECYCLE"]


# ============================================
# BASE
# ============================================

class GradeBase(BaseModel):
    """Shared grade fields."""
    code: GradeCode = Field(description="Grade code: A, A-, B, B-, C, C-, RECYCLE")
    name: str = Field(min_length=2, max_length=60, description="Human-readable name")
    rank: int = Field(ge=1, le=10, description="Lower rank = better quality (1=best)")
    is_recyclable: bool = Field(default=False, description="True if this grade goes to recycling/compost")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("rank")
    @classmethod
    def validate_rank_matches_code(cls, v: int, info) -> int:
        # Optionally validate rank-code consistency
        return v


# ============================================
# CREATE
# ============================================

class GradeCreate(GradeBase):
    pass


# ============================================
# UPDATE
# ============================================

class GradeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    rank: int | None = Field(default=None, ge=1, le=10)
    is_recyclable: bool | None = Field(default=None)
    description: str | None = Field(default=None, max_length=500)


# ============================================
# READ
# ============================================

class GradeRead(GradeBase):
    """Returned in API responses."""
    id: int

    model_config = {"from_attributes": True}


# ============================================
# LIST ITEM (with usage stats - computed)
# ============================================

class GradeListItem(BaseModel):
    """Grade with usage statistics."""
    id: int
    code: GradeCode
    name: str
    rank: int
    is_recyclable: bool
    # Computed stats
    total_assets: int = Field(default=0, description="Number of assets with this grade")
    total_lots: int = Field(default=0, description="Number of lots with this grade")

    model_config = {"from_attributes": True}
