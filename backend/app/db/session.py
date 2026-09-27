"""
Database Session and Engine
===========================
Manages the connection to PostgreSQL.

The DATABASE_URL comes from the environment variable set in
docker-compose.yml: postgresql://veggieops:devpassword_change_in_prod@db:5432/veggieops
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator


# --------------------------------------------
# Database URL from environment
# --------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://veggieops:devpassword_change_in_prod@localhost:5432/veggieops"
)

# --------------------------------------------
# Engine - the actual connection to PostgreSQL
# --------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# --------------------------------------------
# Session factory - creates Session objects
# --------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# --------------------------------------------
# Dependency for FastAPI
# --------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in an endpoint:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()