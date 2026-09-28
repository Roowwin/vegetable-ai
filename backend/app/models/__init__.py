from app.models.location import Location, LocationHistory
"""
SQLAlchemy Models Package
=========================
All model classes are registered with app.db.Base when their files
are imported. Alembic uses Base.metadata to generate migrations.
"""

from app.models.people import Farmer, Customer, Employee
from app.models.procurement import (
    PurchaseOrder,
    PurchaseOrderItem,
    CollectionTrip,
    TripStop,
    Delivery,
)
from app.models.inventory import (
    Vegetable,
    Lot,
    Skid,
    Asset,
    Inventory,
    InventoryTransaction,
)
from app.models.quality import Grade, QualityTest, SortResult
from app.models.sales import Price, Sale, SaleItem
from app.models.costs import CostEntry, LaborRecord
from app.models.audit import ProcessingEvent
from app.models.ai import AIQuery, AIToolCall, Forecast
from app.models import enums  # Re-export enums for convenience

__all__ = [
    # Enums
    "enums",
    # People
    "Farmer", "Customer", "Employee",
    # Procurement
    "PurchaseOrder", "PurchaseOrderItem", "CollectionTrip", "TripStop", "Delivery",
    # Inventory
    "Vegetable", "Lot", "Skid", "Asset", "Inventory", "InventoryTransaction",
    # Quality
    "Grade", "QualityTest", "SortResult",
    # Sales
    "Price", "Sale", "SaleItem",
    # Costs
    "CostEntry", "LaborRecord",
    # Audit
    "ProcessingEvent",
    # AI
    "AIQuery", "AIToolCall", "Forecast",
]
