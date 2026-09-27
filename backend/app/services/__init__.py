"""
Services Package
================
Business logic layer between HTTP routes and the database.

Each service:
- Takes a SQLAlchemy Session in its constructor
- Provides methods for CRUD + business logic
- Returns either ORM models or Pydantic schemas
- Handles pagination, filtering, and error cases
"""
