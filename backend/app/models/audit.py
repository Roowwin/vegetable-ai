"""
Audit Models
============
Processing events log.

Every significant action on a lot, asset, or sale creates a row here.
This is our audit trail — invaluable for debugging, cost analysis, and AI training data.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProcessingEvent(Base):
    """
    An event in the lifecycle of a lot, asset, or sale.
    
    Examples: LotRegistered, GradeAssigned, SaleRecorded.
    """
    __tablename__ = "processing_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    
    # Subject of the event (polymorphic — pick one)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), index=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    sale_id: Mapped[int | None] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"))
    
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    
    event_data: Mapped[dict | None] = mapped_column(JSON)  # Flexible payload
    notes: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_events_lot_created", "lot_id", "created_at"),
        Index("ix_events_type_created", "event_type", "created_at"),
    )
