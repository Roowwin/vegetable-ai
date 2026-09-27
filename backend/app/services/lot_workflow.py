"""
Lot Workflow / State Machine
============================
Defines valid status transitions for vegetable lots and validation logic.

Design Principles:
- Strict state machine (invalid transitions raise errors)
- Every transition is auditable (logged to processing_events)
- Some transitions require additional data (grade_id, etc.)
- Sales-driven statuses (PartiallySold, FullySold) are computed, not set

Status Flow:
    REGISTERED → SKIDDED → SORTED → TESTED → GRADED → IN_INVENTORY
                                                          ↓
                                                       ON_SALE
                                                          ↓
                            PARTIALLY_SOLD → FULLY_SOLD → CLOSED

Terminal States: CLOSED, RECYCLED (only for waste-only lots)
"""

from enum import Enum
from typing import Optional


class LotState(str, Enum):
    """All possible lot statuses."""
    REGISTERED = "Registered"
    SKIDDED = "Skidded"
    SORTED = "Sorted"
    TESTED = "Tested"
    GRADED = "Graded"
    IN_INVENTORY = "InInventory"
    ON_SALE = "OnSale"
    PARTIALLY_SOLD = "PartiallySold"
    FULLY_SOLD = "FullySold"
    CLOSED = "Closed"
    RECYCLED = "Recycled"


# ============================================
# TRANSITION RULES
# ============================================
# Map: current_state -> list of allowed next states
# Empty list = terminal state

LOT_TRANSITIONS: dict[LotState, list[LotState]] = {
    LotState.REGISTERED: [LotState.SKIDDED],
    LotState.SKIDDED: [LotState.SORTED],
    LotState.SORTED: [LotState.TESTED],
    LotState.TESTED: [LotState.GRADED],
    LotState.GRADED: [LotState.IN_INVENTORY],
    LotState.IN_INVENTORY: [LotState.ON_SALE, LotState.CLOSED],
    LotState.ON_SALE: [
        LotState.PARTIALLY_SOLD,
        LotState.FULLY_SOLD,
        LotState.CLOSED,
        LotState.IN_INVENTORY,  # Can pull from sale temporarily
    ],
    LotState.PARTIALLY_SOLD: [
        LotState.FULLY_SOLD,
        LotState.CLOSED,
        LotState.IN_INVENTORY,  # Pull remaining stock
    ],
    LotState.FULLY_SOLD: [LotState.CLOSED],
    LotState.CLOSED: [],       # Terminal
    LotState.RECYCLED: [],     # Terminal
}


# ============================================
# TRANSITION REQUIREMENTS
# ============================================
# Some transitions require additional data to be valid

TRANSITION_REQUIREMENTS: dict[tuple[LotState, LotState], list[str]] = {
    # Transitioning to GRADED requires a grade_id
    (LotState.TESTED, LotState.GRADED): ["grade_id"],
    # Transitioning to IN_INVENTORY requires location
    (LotState.GRADED, LotState.IN_INVENTORY): ["location"],
}


# ============================================
# EVENT TYPES (for processing_events log)
# ============================================

class LotEventType(str, Enum):
    """Event types logged to processing_events for audit trail."""
    LOT_REGISTERED = "LotRegistered"
    LOT_SKIDDED = "LotSkidded"
    LOT_SORTED = "LotSorted"
    LOT_TESTED = "LotTested"
    LOT_GRADED = "LotGraded"
    LOT_INVENTORIED = "LotInventoried"
    LOT_PUT_ON_SALE = "LotPutOnSale"
    LOT_PULLED_FROM_SALE = "LotPulledFromSale"
    LOT_PARTIALLY_SOLD = "LotPartiallySold"
    LOT_FULLY_SOLD = "LotFullySold"
    LOT_CLOSED = "LotClosed"
    LOT_RECYCLED = "LotRecycled"
    GRADE_ASSIGNED = "GradeAssigned"


# Map: transition -> event type to log
TRANSITION_EVENT_MAP: dict[tuple[LotState, LotState], LotEventType] = {
    (LotState.REGISTERED, LotState.SKIDDED): LotEventType.LOT_SKIDDED,
    (LotState.SKIDDED, LotState.SORTED): LotEventType.LOT_SORTED,
    (LotState.SORTED, LotState.TESTED): LotEventType.LOT_TESTED,
    (LotState.TESTED, LotState.GRADED): LotEventType.LOT_GRADED,
    (LotState.GRADED, LotState.IN_INVENTORY): LotEventType.LOT_INVENTORIED,
    (LotState.IN_INVENTORY, LotState.ON_SALE): LotEventType.LOT_PUT_ON_SALE,
    (LotState.ON_SALE, LotState.IN_INVENTORY): LotEventType.LOT_PULLED_FROM_SALE,
    (LotState.ON_SALE, LotState.PARTIALLY_SOLD): LotEventType.LOT_PARTIALLY_SOLD,
    (LotState.ON_SALE, LotState.FULLY_SOLD): LotEventType.LOT_FULLY_SOLD,
    (LotState.PARTIALLY_SOLD, LotState.FULLY_SOLD): LotEventType.LOT_FULLY_SOLD,
    (LotState.FULLY_SOLD, LotState.CLOSED): LotEventType.LOT_CLOSED,
    (LotState.IN_INVENTORY, LotState.CLOSED): LotEventType.LOT_CLOSED,
    (LotState.PARTIALLY_SOLD, LotState.CLOSED): LotEventType.LOT_CLOSED,
}


# ============================================
# VALIDATION FUNCTIONS
# ============================================

class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""
    def __init__(self, current_state: str, new_state: str):
        self.current_state = current_state
        self.new_state = new_state
        super().__init__(
            f"Cannot transition from '{current_state}' to '{new_state}'"
        )


class MissingTransitionDataError(Exception):
    """Raised when required data for a transition is missing."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(
            f"Missing required data for transition: {', '.join(missing_fields)}"
        )


def can_transition(current: str, new: str) -> bool:
    """Check if a transition is allowed without raising an error."""
    try:
        current_state = LotState(current)
        new_state = LotState(new)
    except ValueError:
        return False

    allowed = LOT_TRANSITIONS.get(current_state, [])
    return new_state in allowed


def validate_transition(
    current: str,
    new: str,
    transition_data: Optional[dict] = None,
) -> tuple[LotState, LotState]:
    """
    Validate a state transition.

    Raises:
        InvalidTransitionError: if transition is not allowed
        MissingTransitionDataError: if required data is missing

    Returns:
        Tuple of (current_state, new_state) as LotState enums
    """
    transition_data = transition_data or {}

    try:
        current_state = LotState(current)
        new_state = LotState(new)
    except ValueError as e:
        raise InvalidTransitionError(current, new) from e

    # Check transition is allowed
    allowed = LOT_TRANSITIONS.get(current_state, [])
    if new_state not in allowed:
        raise InvalidTransitionError(current, new)

    # Check required data
    required = TRANSITION_REQUIREMENTS.get((current_state, new_state), [])
    missing = [field for field in required if field not in transition_data or transition_data[field] is None]
    if missing:
        raise MissingTransitionDataError(missing)

    return current_state, new_state


def get_allowed_transitions(current: str) -> list[str]:
    """Get list of allowed next states from the current state."""
    try:
        current_state = LotState(current)
    except ValueError:
        return []
    return [s.value for s in LOT_TRANSITIONS.get(current_state, [])]


def is_terminal_state(state: str) -> bool:
    """Check if a state is terminal (no further transitions allowed)."""
    return can_transition(state, state) is False and len(get_allowed_transitions(state)) == 0


def get_event_type(current: str, new: str) -> Optional[LotEventType]:
    """Get the event type to log for a given transition."""
    try:
        current_state = LotState(current)
        new_state = LotState(new)
    except ValueError:
        return None
    return TRANSITION_EVENT_MAP.get((current_state, new_state))
