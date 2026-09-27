"""
SQLAlchemy Declarative Base
===========================
Every model in our application inherits from this Base class.

This file should be imported BEFORE any models are defined,
because SQLAlchemy needs to know about all model classes
when Alembic autogenerates migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All our models (Lot, Farmer, Sale, etc.) will inherit from this.
    SQLAlchemy uses this to track all model classes for migrations.
    """
    pass


# Import all models here so SQLAlchemy registers them.
# This MUST be at the bottom of the file, after Base is defined.
# We add these imports in Part B when we create the models.
# For now, this list is empty — that's fine.