"""
Base Service Class
==================
Common patterns shared by all services.
"""

from typing import Generic, TypeVar, Type
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Type variables for generic CRUD
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service providing common CRUD operations.
    
    Subclasses should set:
    - model: The SQLAlchemy model class
    """
    
    model: Type[ModelType]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, id: int) -> ModelType | None:
        """Get one record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: bool | None = None,
    ) -> tuple[list[ModelType], int]:
        """
        List records with pagination.
        
        Returns (items, total_count).
        """
        query = self.db.query(self.model)
        
        if is_active is not None and hasattr(self.model, "is_active"):
            query = query.filter(self.model.is_active == is_active)
        
        total = query.count()
        items = query.order_by(self.model.id).offset(skip).limit(limit).all()
        return items, total
    
    def create(self, schema: CreateSchemaType) -> ModelType:
        """Create a new record from schema."""
        obj = self.model(**schema.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: int, schema: UpdateSchemaType) -> ModelType | None:
        """Update a record (partial update)."""
        obj = self.get(id)
        if not obj:
            return None
        
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(obj, key, value)
        
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def soft_delete(self, id: int) -> bool:
        """
        Soft delete: set is_active=False instead of removing.
        Returns True if deleted, False if not found.
        """
        obj = self.get(id)
        if not obj:
            return False
        if hasattr(obj, "is_active"):
            obj.is_active = False
            self.db.commit()
        return True
    
    def hard_delete(self, id: int) -> bool:
        """Actually remove the record. Use with caution."""
        obj = self.get(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
