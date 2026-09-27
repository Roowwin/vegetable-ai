"""
Inventory Service
=================
Current stock management and transaction tracking.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import Inventory, InventoryTransaction, Asset
from app.models.quality import Grade
# Vegetable is defined in inventory.py (not its own module)
# (no import needed - we don't actually use Vegetable in this service)
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryTransactionCreate,
)
from app.services.base import BaseService


class InventoryService(BaseService[Inventory, InventoryCreate, InventoryUpdate]):
    """Service for inventory operations."""

    model = Inventory

    def __init__(self, db: Session):
        super().__init__(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        is_available: bool | None = None,
        location: str | None = None,
        vegetable_id: int | None = None,
        expiring_within_days: int | None = None,
    ) -> tuple[list[Inventory], int]:
        """List inventory with filters."""
        query = self.db.query(Inventory)

        if is_available is not None:
            query = query.filter(Inventory.is_available == is_available)
        if location:
            query = query.filter(Inventory.location == location)
        if vegetable_id:
            query = query.join(Asset, Inventory.asset_id == Asset.id).filter(
                Asset.vegetable_id == vegetable_id
            )
        if expiring_within_days is not None:
            from datetime import timedelta
            cutoff = datetime.now() + timedelta(days=expiring_within_days)
            query = query.filter(Inventory.expires_at <= cutoff)

        total = query.count()
        items = query.order_by(Inventory.expires_at.asc().nullslast()).offset(skip).limit(limit).all()
        return items, total

    def record_transaction(
        self,
        inventory_id: int,
        txn_type: str,
        qty_change_kg: Decimal | None = None,
        qty_change_units: int | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> InventoryTransaction:
        """Record an inventory transaction (Received, Sold, Adjustment, etc.)."""
        inv = self.get(inventory_id)
        if not inv:
            raise ValueError(f"Inventory {inventory_id} not found")

        txn = InventoryTransaction(
            inventory_id=inventory_id,
            txn_type=txn_type,
            qty_change_kg=qty_change_kg,
            qty_change_units=qty_change_units,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by,
        )
        self.db.add(txn)

        # Update inventory quantities
        if qty_change_kg is not None and inv.quantity_kg is not None:
            inv.quantity_kg = (inv.quantity_kg or Decimal("0")) + qty_change_kg
        if qty_change_units is not None and inv.quantity_units is not None:
            inv.quantity_units = (inv.quantity_units or 0) + qty_change_units

        # Mark unavailable if quantity hits zero
        if inv.quantity_kg is not None and inv.quantity_kg <= 0:
            inv.is_available = False

        self.db.commit()
        self.db.refresh(txn)
        return txn

    def get_total_value(self) -> Decimal:
        """Calculate total inventory value (quantity * acquisition cost proxy)."""
        result = self.db.query(
            func.coalesce(func.sum(Inventory.quantity_kg), 0)
        ).filter(
            Inventory.is_available == True
        ).scalar()
        return Decimal(str(result or 0))

    def get_expiring_soon(self, days: int = 7) -> "list[Inventory]":
        """Get inventory items expiring within N days."""
        from datetime import timedelta
        cutoff = datetime.now() + timedelta(days=days)
        return (
            self.db.query(Inventory)
            .filter(
                Inventory.is_available == True,
                Inventory.expires_at.isnot(None),
                Inventory.expires_at <= cutoff,
            )
            .all()
        )
