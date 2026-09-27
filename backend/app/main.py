"""
VeggieOps AI — Backend Application Entry Point
==============================================
This is the FastAPI application that powers our backend.
"""

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------
# Application setup
# --------------------------------------------

app = FastAPI(
    title="VeggieOps AI API",
    description="AI-powered backend for vegetable resale businesses",
    version="0.1.0",
    docs_url="/docs",        # Interactive API docs (Swagger UI)
    redoc_url="/redoc",      # Alternative API docs
)

# --------------------------------------------
# CORS Configuration
# --------------------------------------------
# CORS = Cross-Origin Resource Sharing
# Without this, browsers block our frontend (localhost:3000)
# from calling our backend (localhost:8000).
# In production, replace "*" with your actual frontend domain.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)


# --------------------------------------------
# Health Check Endpoint
# --------------------------------------------
# Used by Docker healthcheck and frontend connection test.

@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    """
    Check that the API is running.
    
    Returns basic system information including timestamp.
    """
    return {
        "status": "healthy",
        "service": "VeggieOps AI",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "milestone": "2 (Part B — Backend Hello World)",
    }


# --------------------------------------------
# Root Endpoint
# --------------------------------------------
# A friendly landing page for anyone hitting the API directly.

@app.get("/", tags=["system"])
async def root() -> dict:
    """
    Welcome endpoint. Points users to the interactive API docs.
    """
    return {
        "message": "Welcome to VeggieOps AI API",
        "docs": "/docs",
        "health": "/api/health",
    }
@app.get("/api/hello/{name}", tags=["demo"])
async def hello(name: str) -> dict:
    """
    A demo endpoint to test hot reload.
    """
    return {"message": f"Hello, {name}! Welcome to VeggieOps AI."}


# --------------------------------------------
# Database Connection Test (Coming in Milestone 3)
# --------------------------------------------
# For now, we just verify the API runs.
# In Milestone 3, we'll add a /api/db-test endpoint that
# actually queries Postgres to prove the connection works.
