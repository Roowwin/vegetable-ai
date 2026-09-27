"""
Lot Transition Endpoints
=========================
HTTP endpoints for the lot workflow state machine.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, not_found
from app.schemas.workflow import LotTransitionRequest, LotTransitionResponse, LotAllowedTransitions
from app.services.lot_service import LotService

router = APIRouter(prefix="/api/lots/{lot_code}/transitions", tags=["Lot Workflow"])


@router.get("", summary="Get transition history for a lot")
async def get_transitions(lot_code: str, db: DbSession):
    """
    Get the full transition history (audit log) for a lot.

    Returns all ProcessingEvents for this lot, ordered chronologically.
    """
    service = LotService(db)
    try:
        history = service.get_transition_history(lot_code)
        return {
            "lot_code": lot_code,
            "event_count": len(history),
            "events": history,
        }
    except ValueError:
        raise not_found("Lot", lot_code)


@router.get("/allowed", summary="Get allowed transitions from current status")
async def get_allowed_transitions(lot_code: str, db: DbSession):
    """
    Get the list of valid next statuses for a lot.

    Returns an empty list if the lot is in a terminal state (Closed, Recycled).
    """
    service = LotService(db)
    try:
        allowed = service.get_allowed_transitions(lot_code)
        lot = service.get_by_code(lot_code)
        return LotAllowedTransitions(
            lot_code=lot_code,
            current_status=lot.status,
            allowed_transitions=allowed,
            is_terminal=len(allowed) == 0,
        )
    except ValueError:
        raise not_found("Lot", lot_code)


@router.post("", response_model=LotTransitionResponse, summary="Transition a lot to a new status")
async def transition_lot(lot_code: str, data: LotTransitionRequest, db: DbSession):
    """
    Perform a state transition on a lot.

    The new_status must be in the allowed transitions for the lot's current status.
    Some transitions require additional data:
    - To "Graded": grade_id is required
    - To "InInventory": location is required

    Returns 400 if the transition is invalid or required data is missing.
    """
    service = LotService(db)
    try:
        result = service.transition_lot(
            lot_code=lot_code,
            new_status=data.new_status,
            employee_id=data.employee_id,
            notes=data.notes,
            grade_id=data.grade_id,
            location=data.location,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "transition_failed",
                "message": str(e),
                "lot_code": lot_code,
                "requested_status": data.new_status,
            },
        )
