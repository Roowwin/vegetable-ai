"""
Location Service
================
Business logic for physical location management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models.location import Location, LocationHistory
from app.models.inventory import Lot, Asset, Inventory, InventoryTransaction
from app.models.audit import ProcessingEvent
from app.services.base import BaseService


class LocationService(BaseService):
    """Service for managing physical locations."""
    
    model = Location
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        location_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list, int]:
        """List locations with filters."""
        query = self.db.query(Location)
        if location_type:
            query = query.filter(Location.location_type == location_type)
        if is_active is not None:
            query = query.filter(Location.is_active == is_active)
        
        total = query.count()
        items = query.order_by(Location.location_type, Location.name).offset(skip).limit(limit).all()
        return items, total
    
    def get_by_code(self, code: str) -> Location | None:
        """Find a location by its code (e.g., 'COLD_ROOM_A')."""
        return self.db.query(Location).filter(Location.code == code).first()
    
    def get_contents(self, location_id: int) -> dict:
        """Get all lots and assets currently at this location."""
        # Lots at this location
        lots = self.db.query(Lot).filter(Lot.current_location_id == location_id).all()
        
        # Assets at this location
        assets = self.db.query(Asset).filter(Asset.current_location_id == location_id).all()
        
        # Calculate totals
        total_lot_weight = sum(lot.total_weight_kg or 0 for lot in lots)
        total_asset_weight = sum(asset.weight_kg or 0 for asset in assets if asset.weight_kg)
        
        return {
            "location_id": location_id,
            "lot_count": len(lots),
            "asset_count": len(assets),
            "total_weight_kg": float(total_lot_weight + total_asset_weight),
            "lots": [
                {
                    "id": lot.id,
                    "lot_code": lot.lot_code,
                    "status": lot.status,
                    "weight_kg": float(lot.total_weight_kg),
                    "vegetable_name": lot.vegetable.name if lot.vegetable else None,
                }
                for lot in lots
            ],
            "assets": [
                {
                    "id": asset.id,
                    "asset_code": asset.asset_code,
                    "weight_kg": float(asset.weight_kg) if asset.weight_kg else None,
                }
                for asset in assets
            ],
        }
    
    def get_history(self, location_id: int, limit: int = 50) -> list:
        """Get recent movement history for a location."""
        return (
            self.db.query(LocationHistory)
            .filter(LocationHistory.to_location_id == location_id)
            .order_by(LocationHistory.moved_at.desc())
            .limit(limit)
            .all()
        )


def record_location_movement(
    db: Session,
    asset_id: Optional[int],
    lot_id: Optional[int],
    from_location_id: Optional[int],
    to_location_id: int,
    moved_by: Optional[int],
    reason: str = "Manual move",
    notes: Optional[str] = None,
) -> LocationHistory:
    """
    Record a location movement in the audit log AND update current_location.
    
    This is the single function to use when moving things. It:
    1. Creates a LocationHistory record
    2. Updates the asset's current_location_id (if asset_id given)
    3. Updates the lot's current_location_id (if lot_id given)
    """
    # Create history record
    history = LocationHistory(
        asset_id=asset_id,
        lot_id=lot_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        moved_by=moved_by,
        reason=reason,
        notes=notes,
    )
    db.add(history)
    
    # Update current location
    if asset_id:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            asset.current_location_id = to_location_id
    if lot_id:
        lot = db.query(Lot).filter(Lot.id == lot_id).first()
        if lot:
            lot.current_location_id = to_location_id
    
    return history
