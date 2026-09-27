"""
Vegetable Endpoints
====================
Catalog management.
"""

from fastapi import APIRouter, Query, status, Depends
from typing import Annotated

from app.api.deps import DbSession, PaginationParams, paginated_response, not_found
from app.schemas.vegetable import VegetableCreate, VegetableUpdate, VegetableRead, VegetableListItem
from app.services.vegetable_service import VegetableService

router = APIRouter(prefix="/api/vegetables", tags=["Vegetables"])


@router.get("", summary="List vegetables")
async def list_vegetables(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search by name (partial match)"),
):
    """List vegetables in the catalog."""
    service = VegetableService(db)
    vegetables, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        category=category,
        search=search,
    )
    items = [VegetableListItem.model_validate(v) for v in vegetables]
    return paginated_response(items, total, pagination.skip, pagination.limit)


@router.get("/categories", summary="List all categories in use")
async def list_categories(db: DbSession):
    """Get all distinct vegetable categories currently in the catalog."""
    service = VegetableService(db)
    return {"categories": service.list_categories()}


@router.get("/{vegetable_id}", response_model=VegetableRead, summary="Get vegetable details")
async def get_vegetable(vegetable_id: int, db: DbSession):
    service = VegetableService(db)
    vegetable = service.get(vegetable_id)
    if not vegetable:
        raise not_found("Vegetable", vegetable_id)
    return vegetable


@router.post("", response_model=VegetableRead, status_code=status.HTTP_201_CREATED)
async def create_vegetable(data: VegetableCreate, db: DbSession):
    service = VegetableService(db)
    return service.create(data)


@router.patch("/{vegetable_id}", response_model=VegetableRead)
async def update_vegetable(vegetable_id: int, data: VegetableUpdate, db: DbSession):
    service = VegetableService(db)
    vegetable = service.update(vegetable_id, data)
    if not vegetable:
        raise not_found("Vegetable", vegetable_id)
    return vegetable
