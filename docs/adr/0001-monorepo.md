# ADR-0001: Use a Monorepo Structure

**Status:** Accepted
**Date:** 2024-03-15
**Deciders:** VeggieOps AI Contributors

## Context

VeggieOps AI consists of multiple distinct components:

- A FastAPI backend (Python)
- A Next.js frontend (TypeScript)
- An AI agent module (Python)
- ML training and inference code (Python)
- Database migrations (SQL)
- Infrastructure configuration (Docker Compose)
- Documentation (Markdown)

We need to decide: **separate repositories per component, or one repository containing all components?**

## Decision

We will use a **single monorepo** with the following top-level structure:

```
vegetable-ai/
├── backend/
├── frontend/
├── agent/
├── ml/
├── data/
├── database/
├── infra/
├── scripts/
├── tests/
└── docs/
```

Each subdirectory is independently buildable and deployable, but they share version control, CI/CD configuration, and documentation.

## Consequences

### Easier

- **Single clone to start working.** New contributors get everything.
- **Atomic cross-component changes.** Renaming a backend API used by the frontend is one commit, not two PRs across two repos.
- **Unified versioning.** All components move together; no version compatibility matrix.
- **Shared documentation.** Architecture, ADRs, and decisions live next to the code.
- **Single CI pipeline.** Docker Compose orchestrates the whole stack locally and in any environment.

### Harder

- **Larger clone size.** Mitigated by `.gitignore` excluding `node_modules/`, `__pycache__/`, and model artifacts.
- **Different toolchains.** Python, TypeScript, and Docker live side-by-side; contributors must install multiple toolchains.
- **Coupling risk.** Without discipline, components can become tightly coupled. We mitigate with clear API boundaries.

## Alternatives Considered

### Multi-repo with shared library

Each component in its own repo; shared types/utils in a separate "common" repo.

**Rejected because**: Adds version coordination overhead. For a learning project with one developer, the cost of maintaining multiple repos exceeds the benefit.

### Polyrepo with no sharing

Fully separate repos with no shared code.

**Rejected because**: Forces duplication of types, schemas, and configuration. Atomic changes become impossible.

### Monorepo with build system (Turborepo, Nx)

Use a dedicated monorepo tool for build orchestration.

**Rejected because**: Premature complexity for a project of this size. The components are small enough that plain `docker compose up` is sufficient orchestration. We can add Turborepo later if build times become a problem.

## Notes

This ADR is revisited if any of these become true:

- The repo exceeds 1 GB of tracked files
- Build times exceed 5 minutes for common workflows
- A second developer joins and wants isolated ownership of a component
- We need to release components independently (e.g., the dashboard as a SaaS)
