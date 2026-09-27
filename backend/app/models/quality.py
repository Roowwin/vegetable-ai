"""
Quality Models
==============
Grades, quality tests, sort results.

Grades (A, A-, B, B-, C, C-, RECYCLE) are pre-seeded.
Tests record the inspection that determined an asset's grade.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Grade(Base):
    """
    A quality grade in the hierarchy.
    
    Seeded with: A, A-, B, B-, C, C-, RECYCLE (in order).
    rank allows sorting: A=1, A-=2, B=3, ...
    """
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # Lower = better
    is_recyclable: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(Text)


class QualityTest(Base):
    """
    An inspection of an asset that determined its grade.
    
    Parameters stored as JSON for flexibility (size, color, firmness, defects).
    """
    __tablename__ = "quality_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    tester_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False)
    
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    parameters: Mapped[dict | None] = mapped_column(JSON)  # Flexible: {size, color, firmness, defects}
    comments: Mapped[str | None] = mapped_column(Text)
    
    # Was this test superseded by a later test?
    superseded_by_id: Mapped[int | None] = mapped_column(ForeignKey("quality_tests.id"))

    # Relationships
    asset = relationship("Asset", back_populates="quality_tests")
    grade = relationship("Grade", lazy="selectin")
    tester = relationship("Employee", lazy="selectin")


class SortResult(Base):
    """
    Result of sorting a lot or skid into sellable vs damaged categories.
    
    Happens BEFORE grading — separates the obviously bad from the candidate-good.
    """
    __tablename__ = "sort_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), nullable=False, index=True)
    skid_id: Mapped[int | None] = mapped_column(ForeignKey("skids.id"))
    
    sorted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sorted_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    
    sellable_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    damaged_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    recycle_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    notes: Mapped[str | None] = mapped_column(Text)
