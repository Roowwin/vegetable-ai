"""
Vegetable Service
=================
Business logic for the vegetable catalog.
"""

from sqlalchemy.orm import Session

from app.models.inventory import Vegetable
from app.schemas.vegetable import VegetableCreate, VegetableUpdate
from app.services.base import BaseService


class VegetableService(BaseService[Vegetable, VegetableCreate, VegetableUpdate]):
    """Service for managing the vegetable catalog."""
    
    model = Vegetable
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        category: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Vegetable], int]:
        """List vegetables with optional filters."""
        query = self.db.query(Vegetable)
        
        if category:
            query = query.filter(Vegetable.category == category.lower())
        if search:
            query = query.filter(Vegetable.name.ilike(f"%{search}%"))
        
        total = query.count()
        items = query.order_by(Vegetable.name).offset(skip).limit(limit).all()
        return items, total
    
    def get_by_name(self, name: str) -> Vegetable | None:
        """Find a vegetable by exact name."""
        return self.db.query(Vegetable).filter(Vegetable.name == name).first()
    
    def list_categories(self) -> "list[str]":
        """Get all distinct categories currently in use."""
        results = (
            self.db.query(Vegetable.category)
            .filter(Vegetable.category.isnot(None))
            .distinct()
            .all()
        )
        return sorted([r[0] for r in results if r[0]])
