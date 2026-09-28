"""
Lot Service
===========
The heart of the business. Tracks lots from acquisition to sale and computes
the true profit and loss for each lot.

This is the most important service in the system.
"""

from __future__ import annotations  # Makes all annotations lazy (fixes list[X] issues)

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import Lot, Skid, Asset, Inventory, InventoryTransaction, Vegetable
from app.models.people import Farmer
from app.models.quality import Grade, QualityTest, SortResult
from app.models.sales import SaleItem
from app.models.costs import CostEntry, LaborRecord
from app.models.audit import ProcessingEvent
from app.models.location import Location, LocationHistory
from app.schemas.lot import (
    LotBase, LotCreate, LotUpdate, LotRead, LotListItem,
    LotProfitLoss, CostBreakdown,
)
from app.schemas.workflow import LotTransitionResponse
from app.services.base import BaseService
from app.services.lot_workflow import (
    LotState, validate_transition, get_event_type, get_allowed_transitions,
    InvalidTransitionError, MissingTransitionDataError, LotEventType,
)


# ============================================
# LOCATION MAPPING CONSTANTS
# ============================================
# Maps vegetable categories to their default storage location
VEGETABLE_STORAGE_LOCATION = {
    "leafy": "COLD_ROOM_A",
    "cruciferous": "COLD_ROOM_A",
    "fruit": "COLD_ROOM_B",
    "root": "DRY_STORAGE",
    "legume": "COLD_ROOM_A",
    "herb": "COLD_ROOM_A",
    "mushroom": "COLD_ROOM_A",
}

# Maps quality grades to their display location
GRADE_SALES_LOCATION = {
    "A": "DISPLAY_FRONT",
    "A-": "DISPLAY_FRONT",
    "B": "SALES_FLOOR",
    "B-": "SALES_FLOOR",
    "C": "DISPLAY_FRONT",  # Discount rack
    "C-": "DISPLAY_FRONT",
    "RECYCLE": "QUARANTINE",
}


class LotService(BaseService[Lot, LotCreate, LotUpdate]):
    """Service for lot operations and P&L analysis."""

    model = Lot

    def __init__(self, db: Session):
        super().__init__(db)

    # ============================================
    # CRUD + LIST METHODS
    # ============================================

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        vegetable_id: int | None = None,
        farmer_id: int | None = None,
        min_acquired_at: datetime | None = None,
        max_acquired_at: datetime | None = None,
    ) -> tuple[list[Lot], int]:
        """List lots with optional filters."""
        query = self.db.query(Lot)

        if status:
            query = query.filter(Lot.status == status)
        if vegetable_id:
            query = query.filter(Lot.vegetable_id == vegetable_id)
        if farmer_id:
            from app.models.procurement import PurchaseOrder
            query = query.join(PurchaseOrder, Lot.purchase_order_id == PurchaseOrder.id).filter(
                PurchaseOrder.farmer_id == farmer_id
            )
        if min_acquired_at:
            query = query.filter(Lot.acquired_at >= min_acquired_at)
        if max_acquired_at:
            query = query.filter(Lot.acquired_at <= max_acquired_at)

        total = query.count()
        items = query.order_by(Lot.acquired_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_code(self, lot_code: str) -> Lot | None:
        """Get a lot by its human-readable code (e.g., 'L-2024-00001')."""
        return self.db.query(Lot).filter(Lot.lot_code == lot_code).first()

    # ============================================
    # P&L COMPUTATION (THE KILLER QUERY)
    # ============================================

    def compute_lot_pnl(self, lot_code: str) -> LotProfitLoss | None:
        """
        Compute detailed profit & loss for a single lot.

        Breakdown includes:
        - Acquisition, transport, processing, storage, selling, waste costs
        - Revenue from all sales
        - Waste percentage and recovery value
        - Gross/net profit and margins (%, per kg)
        """
        lot = self.get_by_code(lot_code)
        if not lot:
            return None

        # ----- COSTS -----
        cost_records = (
            self.db.query(CostEntry)
            .filter(CostEntry.lot_id == lot.id)
            .all()
        )

        costs = CostBreakdown()
        for cr in cost_records:
            amount = cr.amount or Decimal("0")
            category = cr.cost_category or ""
            if category == "Acquisition":
                costs.acquisition += amount
            elif category == "Transport":
                costs.transport += amount
            elif category == "Processing":
                costs.processing += amount
            elif category == "Storage":
                costs.storage += amount
            elif category == "Selling":
                costs.selling += amount
            elif category == "Waste":
                costs.waste += amount
        costs.total = (
            costs.acquisition
            + costs.transport
            + costs.processing
            + costs.storage
            + costs.selling
            + costs.waste
        )

        # ----- REVENUE -----
        revenue_result = (
            self.db.query(func.coalesce(func.sum(SaleItem.line_total), 0))
            .filter(SaleItem.asset_id.in_(
                self.db.query(Asset.id).join(Skid, Asset.skid_id == Skid.id).filter(Skid.lot_id == lot.id)
            ))
            .one()
        )
        total_revenue = Decimal(str(revenue_result[0]))

        sold_weight_result = (
            self.db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
            .filter(SaleItem.asset_id.in_(
                self.db.query(Asset.id).join(Skid, Asset.skid_id == Skid.id).filter(Skid.lot_id == lot.id)
            ))
            .one()
        )
        sold_weight_kg = Decimal(str(sold_weight_result[0]))

        # ----- WASTE -----
        sort_result = (
            self.db.query(SortResult)
            .filter(SortResult.lot_id == lot.id)
            .first()
        )
        waste_kg = Decimal("0")
        waste_recovery_value = Decimal("0")
        if sort_result:
            waste_kg = (sort_result.damaged_kg or Decimal("0")) + (sort_result.recycle_kg or Decimal("0"))
            if sort_result.recycle_kg and sort_result.recycle_kg > 0:
                waste_recovery_value = sort_result.recycle_kg * Decimal("0.05")

        waste_pct = (
            (waste_kg / lot.total_weight_kg * 100) if lot.total_weight_kg > 0 else Decimal("0")
        )

        # ----- PROFIT CALCULATIONS -----
        gross_profit = total_revenue - costs.total
        gross_margin_pct = (
            (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        )

        allocated_overhead = costs.acquisition * Decimal("0.10")
        net_profit = gross_profit - allocated_overhead
        net_margin_pct = (
            (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        )

        cost_per_kg = (
            costs.total / lot.total_weight_kg if lot.total_weight_kg > 0 else Decimal("0")
        )
        revenue_per_kg = (
            total_revenue / sold_weight_kg if sold_weight_kg > 0 else Decimal("0")
        )
        profit_per_kg = (
            net_profit / sold_weight_kg if sold_weight_kg > 0 else Decimal("0")
        )

        # ----- RELATED INFO -----
        farmer_name = "Unknown"
        if lot.purchase_order_id:
            from app.models.procurement import PurchaseOrder
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == lot.purchase_order_id).first()
            if po and po.farmer_id:
                farmer = self.db.query(Farmer).filter(Farmer.id == po.farmer_id).first()
                if farmer:
                    farmer_name = farmer.name

        vegetable_name = "Unknown"
        if lot.vegetable_id:
            veg = self.db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
            if veg:
                vegetable_name = veg.name

        return LotProfitLoss(
            lot_code=lot.lot_code,
            vegetable_name=vegetable_name,
            farmer_name=farmer_name,
            total_cost=costs,
            cost_per_kg=cost_per_kg,
            total_revenue=total_revenue,
            revenue_per_kg=revenue_per_kg,
            sold_weight_kg=sold_weight_kg,
            waste_kg=waste_kg,
            waste_pct=waste_pct,
            waste_recovery_value=waste_recovery_value,
            gross_profit=gross_profit,
            gross_margin_pct=gross_margin_pct,
            net_profit=net_profit,
            net_margin_pct=net_margin_pct,
            profit_per_kg=profit_per_kg,
            status=lot.status,
            acquired_at=lot.acquired_at,
            closed_at=None,
        )

    # ============================================
    # WORKFLOW METHODS (Milestone 6 Phase B)
    # ============================================

    def transition_lot(
        self,
        lot_code: str,
        new_status: str,
        employee_id: int,
        notes: str | None = None,
        grade_id: int | None = None,
        location: str | None = None,
    ) -> LotTransitionResponse:
        """
        Transition a lot to a new status with validation and audit logging.

        Steps:
        1. Look up the lot
        2. Validate the transition (uses state machine)
        3. Apply the transition (update lot.status)
        4. Create a ProcessingEvent record (audit log)
        5. Handle side effects (create inventory, log grade, etc.)
        6. Auto-move to appropriate location
        7. Commit atomically

        Raises:
            ValueError: if lot not found or transition invalid
        """
        # Step 1: Find the lot
        lot = self.get_by_code(lot_code)
        if not lot:
            raise ValueError(f"Lot {lot_code} not found")

        # Step 2: Validate the transition (raises on invalid)
        transition_data = {
            "grade_id": grade_id,
            "location": location,
        }
        try:
            old_state, new_state = validate_transition(
                current=lot.status,
                new=new_status,
                transition_data=transition_data,
            )
        except (InvalidTransitionError, MissingTransitionDataError) as e:
            raise ValueError(str(e)) from e

        # Step 3: Apply the transition
        previous_status = lot.status
        lot.status = new_state

        # Step 4: Create the processing event (audit log)
        event_type = get_event_type(previous_status, new_state) or LotEventType.LOT_REGISTERED
        event = ProcessingEvent(
            event_type=event_type.value,
            lot_id=lot.id,
            asset_id=None,
            sale_id=None,
            employee_id=employee_id,
            event_data={
                "previous_status": previous_status,
                "new_status": new_status,
            },
            notes=notes,
        )
        self.db.add(event)

        # Step 5: Handle side effects based on the transition
        self._handle_transition_side_effects(lot, new_state, grade_id, location, employee_id)

        # Step 6: Auto-move to appropriate location (Milestone 7)
        self._auto_move_on_transition(lot, new_state, grade_id, employee_id)

        # Step 7: Commit atomically
        self.db.commit()
        self.db.refresh(lot)

        # Step 8: Return response
        return LotTransitionResponse(
            lot_code=lot.lot_code,
            previous_status=previous_status,
            new_status=new_status,
            event_type=event_type.value,
            transitioned_at=datetime.now(timezone.utc).isoformat(),
            transitioned_by_employee_id=employee_id,
        )

    def _handle_transition_side_effects(
        self,
        lot: Lot,
        new_state: LotState,
        grade_id: int | None,
        location: str | None,
        employee_id: int,
    ) -> None:
        """
        Handle side effects of a status transition.

        - On Graded: record the grade assignment as a QualityTest
        - On InInventory: create Inventory record + initial transaction
        - On PutOnSale: ensure pricing exists (placeholder)
        """
        # When Graded: record the grade assignment
        if new_state == LotState.GRADED and grade_id:
            grade = self.db.query(Grade).filter(Grade.id == grade_id).first()
            if grade:
                test = QualityTest(
                    asset_id=None,
                    tester_id=employee_id,
                    grade_id=grade_id,
                    tested_at=datetime.now(timezone.utc),
                    parameters={
                        "lot_id": str(lot.id),
                        "transition_grade": grade.code,
                    },
                    comments=f"Grade assigned during workflow transition",
                    superseded_by_id=None,
                )
                self.db.add(test)

        # When InInventory: create Inventory record + initial transaction
        elif new_state == LotState.IN_INVENTORY:
            existing_inv = (
                self.db.query(Inventory)
                .filter(Inventory.location_id.isnot(None))
                .all()
            )
            # Check if any inventory exists for this lot already
            from app.models.inventory import Inventory
            lot_invs = (
                self.db.query(Inventory)
                .filter(Inventory.asset.has(skid_id=None))  # No asset = lot-level
                .all()
            )
            # For now, only create if no inventory for this lot exists
            has_inventory = any(
                inv.asset and inv.asset.skid and inv.asset.skid.lot_id == lot.id
                for inv in lot_invs if inv.asset
            ) if lot_invs else False

            if not has_inventory:
                inv_location_code = location or "COLD_ROOM_A"
                target_loc = self.db.query(Location).filter(Location.code == inv_location_code).first()
                if not target_loc:
                    target_loc = self.db.query(Location).filter(Location.code == "COLD_ROOM_A").first()

                if target_loc:
                    inv = Inventory(
                        asset_id=None,
                        location_id=target_loc.id,
                        quantity_kg=lot.total_weight_kg,
                        quantity_units=None,
                        available_from=datetime.now(timezone.utc),
                        expires_at=None,
                        is_available=True,
                    )
                    self.db.add(inv)
                    self.db.flush()

                    txn = InventoryTransaction(
                        inventory_id=inv.id,
                        txn_type="Received",
                        qty_change_kg=lot.total_weight_kg,
                        qty_change_units=None,
                        reference_type="lot_arrival",
                        reference_id=lot.id,
                        notes=f"Initial stock from {lot.lot_code}",
                        created_by=employee_id,
                    )
                    self.db.add(txn)

        # When PutOnSale: pricing logic (placeholder for now)
        elif new_state == LotState.ON_SALE:
            # Pricing will be handled in Milestone 9 (Sales system)
            pass

    def _auto_move_on_transition(
        self,
        lot: Lot,
        new_state: LotState,
        grade_id: int | None,
        employee_id: int,
    ) -> None:
        """
        Auto-move lot/assets to the appropriate location based on the transition.
        Creates LocationHistory records for audit.
        """
        # Determine target location code based on transition
        target_code = None

        if new_state == LotState.IN_INVENTORY:
            # Use vegetable's default storage
            veg = self.db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
            if veg and veg.category:
                target_code = VEGETABLE_STORAGE_LOCATION.get(veg.category, "COLD_ROOM_A")
        elif new_state == LotState.ON_SALE:
            # Use grade-based sales location
            if grade_id:
                grade = self.db.query(Grade).filter(Grade.id == grade_id).first()
                if grade:
                    target_code = GRADE_SALES_LOCATION.get(grade.code, "SALES_FLOOR")
            else:
                target_code = "SALES_FLOOR"
        elif new_state == LotState.GRADED and grade_id:
            # After grading, move to appropriate storage based on vegetable
            veg = self.db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
            if veg and veg.category:
                target_code = VEGETABLE_STORAGE_LOCATION.get(veg.category, "COLD_ROOM_A")
        elif new_state == LotState.SKIDDED:
            target_code = "SORT_BENCH"
        elif new_state == LotState.SORTED:
            target_code = "TEST_BENCH"
        elif new_state == LotState.TESTED:
            target_code = "TEST_BENCH"

        if not target_code:
            return  # No auto-move for this transition

        # Find target location
        target_location = self.db.query(Location).filter(Location.code == target_code).first()
        if not target_location:
            return  # Location doesn't exist

        # Record the move for the lot
        from_location_id = lot.current_location_id
        history = LocationHistory(
            asset_id=None,
            lot_id=lot.id,
            from_location_id=from_location_id,
            to_location_id=target_location.id,
            moved_by=employee_id,
            reason=f"Auto-move on transition to {new_state.value}",
        )
        self.db.add(history)
        lot.current_location_id = target_location.id

        # Also move all assets in this lot
        for skid in lot.skids:
            for asset in skid.assets:
                asset_history = LocationHistory(
                    asset_id=asset.id,
                    lot_id=None,
                    from_location_id=asset.current_location_id,
                    to_location_id=target_location.id,
                    moved_by=employee_id,
                    reason=f"Auto-move with lot on {new_state.value}",
                )
                self.db.add(asset_history)
                asset.current_location_id = target_location.id

    def get_transition_history(self, lot_code: str) -> "list[dict]":
        """Get the full transition history for a lot (audit log)."""
        lot = self.get_by_code(lot_code)
        if not lot:
            raise ValueError(f"Lot {lot_code} not found")

        events = (
            self.db.query(ProcessingEvent)
            .filter(
                ProcessingEvent.lot_id == lot.id,
                ProcessingEvent.event_type.in_([
                    "LotRegistered", "LotSkidded", "LotSorted", "LotTested",
                    "LotGraded", "LotInventoried", "LotPutOnSale",
                    "LotPulledFromSale", "LotPartiallySold", "LotFullySold",
                    "LotClosed", "LotRecycled", "GradeAssigned",
                ]),
            )
            .order_by(ProcessingEvent.created_at)
            .all()
        )

        return [
            {
                "event_type": e.event_type,
                "employee_id": e.employee_id,
                "timestamp": e.created_at.isoformat() if e.created_at else None,
                "notes": e.notes,
                "event_data": e.event_data,
            }
            for e in events
        ]

    def get_allowed_transitions(self, lot_code: str) -> "list[str]":
        """Get the list of allowed transitions from a lot's current status."""
        lot = self.get_by_code(lot_code)
        if not lot:
            raise ValueError(f"Lot {lot_code} not found")
        return get_allowed_transitions(lot.status)

    def get_location_history(self, lot_code: str, limit: int = 50) -> "list[dict]":
        """Get the location movement history for a lot."""
        lot = self.get_by_code(lot_code)
        if not lot:
            raise ValueError(f"Lot {lot_code} not found")

        history = (
            self.db.query(LocationHistory)
            .filter(LocationHistory.lot_id == lot.id)
            .order_by(LocationHistory.moved_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "from_location_id": h.from_location_id,
                "to_location_id": h.to_location_id,
                "moved_at": h.moved_at.isoformat() if h.moved_at else None,
                "moved_by": h.moved_by,
                "reason": h.reason,
                "notes": h.notes,
            }
            for h in history
        ]

    def move_lot(
        self,
        lot_code: str,
        to_location_code: str,
        employee_id: int,
        reason: str = "Manual move",
        notes: str | None = None,
    ) -> dict:
        """
        Manually move a lot to a new location.
        Creates a LocationHistory record and updates current_location_id.
        Also moves all assets in the lot.
        """
        lot = self.get_by_code(lot_code)
        if not lot:
            raise ValueError(f"Lot {lot_code} not found")

        # Find target location
        target_location = self.db.query(Location).filter(Location.code == to_location_code).first()
        if not target_location:
            raise ValueError(f"Location '{to_location_code}' not found")

        from_location_id = lot.current_location_id

        # Record the move for the lot
        history = LocationHistory(
            asset_id=None,
            lot_id=lot.id,
            from_location_id=from_location_id,
            to_location_id=target_location.id,
            moved_by=employee_id,
            reason=reason,
            notes=notes,
        )
        self.db.add(history)
        lot.current_location_id = target_location.id

        # Also move all assets
        for skid in lot.skids:
            for asset in skid.assets:
                asset_history = LocationHistory(
                    asset_id=asset.id,
                    lot_id=None,
                    from_location_id=asset.current_location_id,
                    to_location_id=target_location.id,
                    moved_by=employee_id,
                    reason=f"Moved with lot {lot.lot_code}",
                )
                self.db.add(asset_history)
                asset.current_location_id = target_location.id

        self.db.commit()

        return {
            "lot_code": lot.lot_code,
            "from_location_id": from_location_id,
            "to_location": to_location_code,
            "to_location_id": target_location.id,
            "moved_by": employee_id,
            "reason": reason,
        }
