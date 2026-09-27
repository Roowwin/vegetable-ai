"""
Workflow / Transition Schemas
=============================
Request/response models for lot state transitions.
"""

from typing import Optional
from pydantic import BaseModel, Field


class LotTransitionRequest(BaseModel):
    """Request to transition a lot to a new status."""
    new_status: str = Field(description="Target status (e.g., 'Skidded', 'Graded')")
    employee_id: int = Field(gt=0, description="ID of employee performing the transition")
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Optional data that some transitions require
    grade_id: Optional[int] = Field(default=None, gt=0, description="Required when transitioning to 'Graded'")
    location: Optional[str] = Field(default=None, max_length=60, description="Required when transitioning to 'InInventory'")


class LotTransitionResponse(BaseModel):
    """Response after a successful transition."""
    lot_code: str
    previous_status: str
    new_status: str
    event_type: str
    transitioned_at: str
    transitioned_by_employee_id: int


class LotAllowedTransitions(BaseModel):
    """List of allowed transitions from a lot's current status."""
    lot_code: str
    current_status: str
    allowed_transitions: list[str]
    is_terminal: bool
