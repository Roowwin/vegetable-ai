"""
Cost Models
===========
Cost entries and labor records.

All costs are recorded with an allocation_method so we can recompute
allocation across items if the business rules change.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import CostCategory, AllocationMethod


class CostEntry(Base):
    """
    A cost incurred against a lot (or globally for overhead).
    
    Examples: trip fuel, packaging, electricity, equipment rental.
    """
    __tablename__ = "cost_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), index=True)
    
    cost_category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    allocation_method: Mapped[str] = mapped_column(String(32), default=AllocationMethod.FIXED_PER_LOT.value)
    
    incurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Optional reference to source (trip, delivery, etc.)
    reference_type: Mapped[str | None] = mapped_column(String(32))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    
    description: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LaborRecord(Base):
    """
    Time-and-cost record for an employee working on a specific activity.
    
    Examples: 2 hours sorting lot L001 at $15/hr = $30 labor cost.
    """
    __tablename__ = "labor_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), index=True)
    
    activity_type: Mapped[str] = mapped_column(String(40), nullable=False)  # collection, sorting, grading, sales
    
    work_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
