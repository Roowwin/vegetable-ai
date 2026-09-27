"""
Sales Models
============
Prices, sales, sale items.

Sales have a header (Sales) and one or more line items (SaleItems).
Prices are stored separately to support price history.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import SaleStatus, UnitType


class Price(Base):
    """
    A price for a (vegetable, grade, unit_type) combination.
    
    Multiple prices can exist for the same item with different effective dates.
    """
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    vegetable_id: Mapped[int] = mapped_column(ForeignKey("vegetables.id"), nullable=False, index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)  # kg, piece, half, quarter, etc.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    set_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    notes: Mapped[str | None] = mapped_column(Text)


class Sale(Base):
    """
    A sale transaction header.
    
    Total amount is calculated from sale_items but stored for quick queries.
    """
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), index=True)
    
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    status: Mapped[str] = mapped_column(String(32), default=SaleStatus.COMPLETED.value)
    payment_method: Mapped[str | None] = mapped_column(String(30))  # cash, card, mobile, credit
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    sold_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", lazy="selectin")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    """
    One line item in a sale: an asset (or lot) sold in a specific unit type.
    """
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id: Mapped[int | None] = mapped_column(ForeignKey("inventory.id"))
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"))
    vegetable_id: Mapped[int] = mapped_column(ForeignKey("vegetables.id"), nullable=False)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    sale = relationship("Sale", back_populates="items")
