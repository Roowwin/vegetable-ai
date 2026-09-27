"""
Procurement Models
==================
Purchase orders, collection trips, deliveries.

These tables capture everything that happens BEFORE a lot is registered:
- PO creation and lifecycle
- Collection trips (shop drives to farm)
- Deliveries (farmer brings to shop)
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import PurchaseOrderStatus


class PurchaseOrder(Base):
    """
    A formal commitment to buy vegetables from a specific farmer.
    
    One PO can produce multiple Lots (via partial deliveries).
    """
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(32), default=PurchaseOrderStatus.DRAFT.value)
    
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date)
    
    total_expected_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_actual_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    
    payment_terms: Mapped[str | None] = mapped_column(String(64))
    delivery_mode: Mapped[str] = mapped_column(String(32), nullable=False)  # Collection, FarmerDelivery
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    farmer = relationship("Farmer", lazy="selectin")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    """
    A line item on a purchase order: one vegetable type with expected quantity and price.
    """
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    vegetable_id: Mapped[int] = mapped_column(ForeignKey("vegetables.id"), nullable=False)
    
    expected_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    expected_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    received_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    actual_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    vegetable = relationship("Vegetable", lazy="selectin")


class CollectionTrip(Base):
    """
    A trip made by the shop (or driver) to a farm to collect vegetables.
    
    Has its own costs: fuel, vehicle wear, driver time.
    """
    __tablename__ = "collection_trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    vehicle: Mapped[str | None] = mapped_column(String(60))
    
    departed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    fuel_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    other_costs: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", lazy="selectin")
    stops = relationship("TripStop", back_populates="trip", cascade="all, delete-orphan")


class TripStop(Base):
    """
    One stop at a farm during a collection trip.
    
    A single trip may visit multiple farms (or the same farm multiple times).
    """
    __tablename__ = "trip_stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("collection_trips.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id"))  # Farmer as farm reference
    
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    departed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    trip = relationship("CollectionTrip", back_populates="stops")


class Delivery(Base):
    """
    A delivery where the farmer brings vegetables to the shop.
    
    Different cost structure than collection trips (no fuel for shop, possibly delivery fee).
    """
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=False)
    
    arrived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unloaded_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    
    vehicle: Mapped[str | None] = mapped_column(String(60))
    delivery_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farmer = relationship("Farmer", lazy="selectin")
