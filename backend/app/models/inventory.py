"""
Inventory Models
================
Vegetables catalog, lots, skids, assets, inventory tracking.

This is the core of our domain model — every other table relates back to a Lot.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import LotStatus, AssetStatus, InventoryTransactionType


class Vegetable(Base):
    """
    Master catalog of vegetables we sell.
    
    Tracks default unit type and typical shelf life for each vegetable.
    """
    __tablename__ = "vegetables"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(40))  # leafy, root, fruit, etc.
    default_unit_type: Mapped[str] = mapped_column(String(20), default="kg")
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)
    typical_waste_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # e.g., 8.50%
    notes: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Lot(Base):
    """
    The central entity. A quantity of vegetables acquired together from one source.
    
    Most analytics queries (cost, profit) are answered per-lot.
    """
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    vegetable_id: Mapped[int] = mapped_column(ForeignKey("vegetables.id"), nullable=False, index=True)
    
    # Source: either a collection trip, a delivery, or a market purchase (no PO)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)  # collection_trip, delivery, market
    source_id: Mapped[int | None] = mapped_column(Integer)
    
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), default=LotStatus.REGISTERED.value, index=True)
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lots")
    vegetable = relationship("Vegetable", lazy="selectin")
    skids = relationship("Skid", back_populates="lot", cascade="all, delete-orphan")


class Skid(Base):
    """
    A pallet/skid that holds part of a lot after arrival.
    """
    __tablename__ = "skids"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), nullable=False, index=True)
    skid_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    position: Mapped[str | None] = mapped_column(String(40))  # e.g., "Cold Room A, Shelf 3"
    notes: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lot = relationship("Lot", back_populates="skids")
    assets = relationship("Asset", back_populates="skid", cascade="all, delete-orphan")


class Asset(Base):
    """
    An individually tracked item within a lot (for large items: pumpkins, cabbages).
    
    Loose items (tomatoes, leafy greens) stay at the lot level — no asset row.
    """
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    skid_id: Mapped[int | None] = mapped_column(ForeignKey("skids.id", ondelete="CASCADE"), index=True)
    asset_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    dimensions: Mapped[str | None] = mapped_column(String(60))
    
    current_stage: Mapped[str] = mapped_column(String(32), default="Registered")
    status: Mapped[str] = mapped_column(String(32), default=AssetStatus.REGISTERED.value, index=True)
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    skid = relationship("Skid", back_populates="assets")
    quality_tests = relationship("QualityTest", back_populates="asset", cascade="all, delete-orphan")


class Inventory(Base):
    """
    Current stock of an asset (or lot) available for sale.
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    location: Mapped[str] = mapped_column(String(60), default="Main Shop")
    
    quantity_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    quantity_units: Mapped[int | None] = mapped_column(Integer)
    
    available_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    is_available: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    asset = relationship("Asset", lazy="selectin")
    transactions = relationship("InventoryTransaction", back_populates="inventory", cascade="all, delete-orphan")


class InventoryTransaction(Base):
    """
    Audit log of every stock movement.
    
    Every change to inventory creates a transaction row — Received, Sold, Adjustment, etc.
    """
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    txn_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    
    qty_change_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    qty_change_units: Mapped[int | None] = mapped_column(Integer)
    
    reference_type: Mapped[str | None] = mapped_column(String(32))  # sale, adjustment, transfer
    reference_id: Mapped[int | None] = mapped_column(Integer)
    
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")

    __table_args__ = (
        Index("ix_inv_txn_inventory_created", "inventory_id", "created_at"),
    )
