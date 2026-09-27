"""
Shared Dependencies
===================
Common FastAPI dependencies used across all route modules.
"""

from typing import Annotated
from fastapi import Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db


# Type alias for cleaner dependency injection
DbSession = Annotated[Session, Depends(get_db)]


class PaginationParams:
    """Reusable pagination query parameters."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, le=10000, description="Number of records to skip"),
        limit: int = Query(50, ge=1, le=200, description="Max records to return (capped at 200)"),
    ):
        self.skip = skip
        self.limit = limit


def paginated_response(items: list, total: int, skip: int, limit: int) -> dict:
    """Build a standard paginated response."""
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + len(items)) < total,
    }


def not_found(resource: str, identifier: str | int) -> HTTPException:
    """Standard 404 error with helpful message."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "not_found",
            "message": f"{resource} '{identifier}' not found",
            "resource": resource,
            "identifier": str(identifier),
        },
    )
