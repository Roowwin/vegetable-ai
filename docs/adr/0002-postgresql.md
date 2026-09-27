# ADR-0002: Use PostgreSQL as the Primary Database

**Status:** Accepted
**Date:** 2024-03-15
**Deciders:** VeggieOps AI Contributors

## Context

VeggieOps AI needs persistent storage for:

- Farmers, purchase orders, lots, skids, assets (hierarchical procurement data)
- Inventory and inventory transactions (financial-grade audit trail)
- Sales and sale items (transactional integrity required)
- Cost entries (must support complex joins with lots, assets, dates)
- AI queries and tool calls (relational to lots, employees, queries)
- Forecasts (relational to vegetables, grades, time periods)

The data is **highly relational**, with strict consistency requirements for financial records. We need ACID transactions, foreign keys, and powerful JOIN operations.

## Decision

We will use **PostgreSQL 15** as the primary database, running in a Docker container locally and replaceable with a managed PostgreSQL (RDS, Cloud SQL, etc.) in production.

We will access it via **SQLAlchemy 2.x ORM** with **Alembic** for schema migrations.

## Consequences

### Easier

- **ACID compliance.** Every financial transaction is atomic; we never sell an item that's not in stock.
- **Foreign key constraints.** Referential integrity is enforced at the database, not the application.
- **Powerful analytics SQL.** Window functions, CTEs, and complex joins for the analytics dashboard are first-class.
- **Mature ecosystem.** Decades of tooling: pgAdmin, pg_dump, replication, backups.
- **JSON support when needed.** We can store semi-structured data (e.g., quality test parameters) in `JSONB` columns without sacrificing relational joins.
- **Industry standard.** PostgreSQL skills transfer directly to most engineering roles.

### Harder

- **Operational overhead.** We must run a Postgres process (handled by Docker Compose).
- **Schema migrations.** Schema changes require Alembic migrations, not just code changes.
- **Connection pooling.** Required for production; less important for a single-user local app.

## Alternatives Considered

### SQLite

**Rejected because**: SQLite does not support concurrent writes, which is required when the AI agent, ML training jobs, and the backend API all need to write simultaneously. SQLite is also limited in analytics SQL features.

### MongoDB

**Rejected because**: Our data is fundamentally relational. Modelling lots → items → sales → costs in MongoDB would require manual joins in application code, with no referential integrity. The 2020s industry trend has moved back toward PostgreSQL even for semi-structured data, thanks to `JSONB`.

### MySQL/MariaDB

**Rejected because**: PostgreSQL has stronger support for window functions, CTEs, JSONB, and partial indexes, all of which we use for analytics queries. The license and community are also more aligned with our open-source philosophy.

### DuckDB

**Rejected because**: Excellent for analytics but not designed for transactional workloads. We could use DuckDB as a secondary analytical store later, but PostgreSQL handles both OLTP and analytical queries adequately at our scale.

## Notes

This decision is reconsidered if:

- We exceed 100 GB of data (consider partitioning or Citus)
- We need true multi-region replication (consider CockroachDB or Spanner)
- Read load dominates write load 100:1 (consider read replicas)
