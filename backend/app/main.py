"""
VeggieOps AI - Backend Application Entry Point
==============================================
"""

from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app = FastAPI(
    title="VeggieOps AI API",
    description="AI-powered backend for vegetable resale businesses",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "VeggieOps AI",
        "version": "0.3.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "milestone": "3 (Part A - Database Connection)",
    }


@app.get("/", tags=["system"])
async def root() -> dict:
    return {
        "message": "Welcome to VeggieOps AI API",
        "docs": "/docs",
        "health": "/api/health",
        "db_test": "/api/db-test",
    }


@app.get("/api/db-test", tags=["system"])
async def db_test(db: Session = Depends(get_db)) -> dict:
    """
    Verify the backend can connect to PostgreSQL.
    """
    try:
        version_result = db.execute(text("SELECT version()")).fetchone()
        version = version_result[0] if version_result else "unknown"

        db_result = db.execute(text("SELECT current_database()")).fetchone()
        database = db_result[0] if db_result else "unknown"

        # Use parameter binding to avoid quote issues
        count_result = db.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema = :schema"),
            {"schema": "public"}
        ).fetchone()
        table_count = count_result[0] if count_result else 0

        return {
            "status": "connected",
            "database": database,
            "version": version,
            "tables_in_public_schema": table_count,
            "milestone": "3 (Part A - Database Connection)",
            "next_step": "Part B will create 22 tables",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }