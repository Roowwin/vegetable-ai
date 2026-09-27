"""
Common Schemas
==============
Shared schemas used across the API:
- Pagination
- Error responses
- Image references
"""

from datetime import datetime
from typing import Generic, TypeVar, Literal
from pydantic import BaseModel, Field, HttpUrl


# ============================================
# TYPE VARIABLE FOR GENERIC PAGINATION
# ============================================

T = TypeVar("T")


# ============================================
# PAGINATION
# ============================================

class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    skip: int = Field(default=0, ge=0, le=10000, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=200, description="Max records to return (capped at 200)")

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: int = Field(description="Total matching records")
    skip: int
    limit: int
    has_more: bool = Field(description="True if more records exist beyond this page")

    model_config = {"from_attributes": True}


# ============================================
# ERROR RESPONSES
# ============================================

class ErrorDetail(BaseModel):
    """Individual error item."""
    field: str | None = Field(default=None, description="Field name if error is field-specific")
    message: str = Field(description="Human-readable error message")
    code: str | None = Field(default=None, description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(description="Error category")
    message: str = Field(description="Human-readable message")
    details: list[ErrorDetail] | None = Field(default=None, description="Specific error details")
    request_id: str | None = Field(default=None, description="Trace ID for support")

    model_config = {"from_attributes": True}


# ============================================
# IMAGE SUPPORT
# ============================================

# Where does the image live?
ImageSource = Literal["url", "upload", "ai_generated", "external_cdn"]


class ImageInfo(BaseModel):
    """
    Reference to an image attached to an entity.

    Current implementation uses URLs (pointing to Unsplash, CDNs, etc.).
    Future versions can store uploaded files or AI-generated images by changing
    the 'source' field and adjusting the 'url' to point to your storage.
    """
    url: HttpUrl = Field(description="Public URL to the image")
    alt_text: str | None = Field(
        default=None,
        max_length=200,
        description="Accessibility text describing the image"
    )
    width: int | None = Field(default=None, ge=1, le=10000)
    height: int | None = Field(default=None, ge=1, le=10000)
    source: ImageSource = Field(default="url", description="Where this image lives")
    is_primary: bool = Field(default=False, description="Primary image for galleries")
    caption: str | None = Field(default=None, max_length=500)

    model_config = {"from_attributes": True}


# ============================================
# COMMON TIMESTAMPS
# ============================================

class TimestampMixin(BaseModel):
    """Adds created_at/updated_at to response schemas."""
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ============================================
# API RESPONSE METADATA
# ============================================

class APIInfo(BaseModel):
    """Basic API information for the root endpoint."""
    name: str = "VeggieOps AI API"
    version: str
    environment: str
    docs_url: str = "/docs"
    health_url: str = "/api/health"
    timestamp: datetime

    model_config = {"from_attributes": True}
