# ============================================
# VeggieOps AI — Makefile
# ============================================
# Common commands for development and operations.
# Usage: make <target>
#
# On Windows, install Make via:
#   choco install make
#   OR use WSL
#   OR just read this file and run the commands manually in PowerShell.

# --------------------------------------------
# Meta
# --------------------------------------------
.PHONY: help

help: ## Show this help message
	@echo "VeggieOps AI — Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --------------------------------------------
# Setup
# --------------------------------------------
.PHONY: install check-deps

install: ## Install all dependencies (run once after cloning)
	@echo "Installing Python dependencies..."
	cd backend && python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done. Run 'make pull-models' next."

check-deps: ## Verify required tools are installed
	@echo "Checking dependencies..."
	@docker --version || (echo "ERROR: Docker not installed" && exit 1)
	@docker compose version || (echo "ERROR: Docker Compose not installed" && exit 1)
	@git --version || (echo "ERROR: Git not installed" && exit 1)
	@ollama --version || (echo "WARNING: Ollama not installed (needed for AI features)")
	@echo "All required dependencies present."

pull-models: ## Pull the required Ollama models
	ollama pull qwen2.5-coder:1.5b
	ollama pull gemma3:4b
	ollama pull qwen2.5:7b
	ollama pull nomic-embed-text:latest

# --------------------------------------------
# Development
# --------------------------------------------
.PHONY: up down restart logs ps shell

up: ## Start all services (Postgres + Backend + Frontend)
	docker compose up -d
	@echo "Services starting. Check status with 'make ps'."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "Database UI: http://localhost:8080"

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## View logs from all services (Ctrl+C to exit)
	docker compose logs -f

ps: ## List running services
	docker compose ps

shell-backend: ## Open a shell in the backend container
	docker compose exec backend /bin/bash

shell-db: ## Open a PostgreSQL shell
	docker compose exec postgres psql -U veggieops -d veggieops

# --------------------------------------------
# Database
# --------------------------------------------
.PHONY: db-create db-migrate db-upgrade db-downgrade db-seed db-reset

db-create: ## Create the database (first time only)
	docker compose exec postgres createdb -U veggieops veggieops || true

db-migrate: ## Create a new Alembic migration (after model changes)
	cd backend && alembic revision --autogenerate -m "migration message"

db-upgrade: ## Apply all pending migrations
	cd backend && alembic upgrade head

db-downgrade: ## Rollback the last migration
	cd backend && alembic downgrade -1

db-seed: ## Seed the database with sample data (Milestone 4)
	cd backend && python -m scripts.seed_data

db-reset: ## Drop and recreate the database (WARNING: destroys data)
	docker compose down -v
	docker compose up -d postgres
	@echo "Database reset. Run 'make db-upgrade && make db-seed' to reinitialize."

# --------------------------------------------
# Testing
# --------------------------------------------
.PHONY: test test-backend test-agent test-coverage

test: test-backend ## Run all tests

test-backend: ## Run backend unit and integration tests
	cd backend && pytest -v

test-agent: ## Run AI agent evaluation tests (Milestone 15)
	cd tests && python -m pytest agent/ -v

test-coverage: ## Run tests with coverage report
	cd backend && pytest --cov=app --cov-report=html

# --------------------------------------------
# Code Quality
# --------------------------------------------
.PHONY: lint format typecheck

lint: ## Run linters
	cd backend && ruff check .
	cd frontend && npm run lint

format: ## Auto-format code
	cd backend && ruff format .
	cd frontend && npm run format

typecheck: ## Run type checkers
	cd backend && mypy app/

# --------------------------------------------
# AI / Ollama
# --------------------------------------------
.PHONY: ollama-status ollama-test ollama-logs

ollama-status: ## List downloaded Ollama models
	ollama list

ollama-test: ## Test all three AI models with a simple prompt
	@echo "Testing Model 1 (Router)..."
	@ollama run qwen2.5-coder:1.5b "Output JSON: {\"status\":\"ok\"}"
	@echo ""
	@echo "Testing Model 2 (General)..."
	@ollama run gemma3:4b "Say hello in one sentence"
	@echo ""
	@echo "Testing Model 3 (Advanced)..."
	@ollama run qwen2.5:7b "Explain profit margin in one sentence"

ollama-gpu: ## Show current GPU usage
	nvidia-smi

# --------------------------------------------
# Documentation
# --------------------------------------------
.PHONY: docs-serve docs-build

docs-serve: ## Serve documentation locally
	@echo "Documentation is in /docs. Open architecture.md in your editor."

# --------------------------------------------
# Cleanup
# --------------------------------------------
.PHONY: clean clean-all

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.mypy_cache backend/.ruff_cache 2>/dev/null || true
	rm -rf frontend/.next frontend/out 2>/dev/null || true
	@echo "Cleaned."

clean-all: clean ## Also remove Docker volumes (DESTROYS DATABASE)
	docker compose down -v
	@echo "WARNING: All data destroyed."
