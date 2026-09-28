"""
Location Models
===============
Physical locations in the shop where lots and assets are stored.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Boolean, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Location(Base):
    """A physical location in the shop."""
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    location_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    temperature_zone: Mapped[str | None] = mapped_column(String(20))
    capacity_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LocationHistory(Base):
    """Audit log of when assets/lots move between locations."""
    __tablename__ = "location_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id", ondelete="CASCADE"), index=True
    )

    from_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    to_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    moved_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))

    reason: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "(asset_id IS NOT NULL) OR (lot_id IS NOT NULL)",
            name="check_location_history_subject",
        ),
    )
