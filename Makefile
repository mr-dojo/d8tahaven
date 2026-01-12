.PHONY: help install dev test lint format clean migrate services services-down services-logs api worker flower db-shell redis-shell

# Default target
.DEFAULT_GOAL := help

# ============================================================================
# Help
# ============================================================================

help:  ## Show this help message
	@echo "Personal Data Collector (PDC) - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Setup
# ============================================================================

install:  ## Install dependencies with Poetry
	@echo "Installing dependencies..."
	poetry install
	@echo "Done! Run 'make dev' to start development environment."

install-dev:  ## Install dependencies including dev tools
	@echo "Installing all dependencies (including dev)..."
	poetry install --with dev,test
	@echo "Done!"

update:  ## Update dependencies
	@echo "Updating dependencies..."
	poetry update
	@echo "Done!"

# ============================================================================
# Development Environment
# ============================================================================

dev:  ## Start development environment (services + API + worker)
	@echo "Starting development environment..."
	@echo "1. Starting Docker services..."
	docker-compose -f infrastructure/docker-compose.yml up -d
	@echo "2. Waiting for services to be ready..."
	@sleep 5
	@echo "3. Services ready! Run 'make api' and 'make worker' in separate terminals."

services:  ## Start Docker services (PostgreSQL, Redis, Flower)
	@echo "Starting Docker services..."
	docker-compose -f infrastructure/docker-compose.yml up -d
	@echo "Services started!"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - Flower: http://localhost:5555"

services-down:  ## Stop Docker services
	@echo "Stopping Docker services..."
	docker-compose -f infrastructure/docker-compose.yml down
	@echo "Services stopped!"

services-logs:  ## View Docker services logs
	docker-compose -f infrastructure/docker-compose.yml logs -f

services-restart:  ## Restart Docker services
	@echo "Restarting Docker services..."
	docker-compose -f infrastructure/docker-compose.yml restart
	@echo "Services restarted!"

services-reset:  ## Reset Docker services (WARNING: Deletes all data!)
	@echo "WARNING: This will delete all data in PostgreSQL and Redis!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f infrastructure/docker-compose.yml down -v; \
		echo "All data deleted!"; \
	else \
		echo "Cancelled."; \
	fi

# ============================================================================
# Run Services
# ============================================================================

api:  ## Start FastAPI server (with hot reload)
	@echo "Starting FastAPI server on http://localhost:8000..."
	poetry run uvicorn src.capture.api:app --reload --host 0.0.0.0 --port 8000

worker:  ## Start Celery worker
	@echo "Starting Celery worker..."
	poetry run celery -A src.enrichment.tasks worker --loglevel=info --concurrency=4

flower:  ## Open Flower monitoring dashboard
	@echo "Opening Flower dashboard at http://localhost:5555..."
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Open http://localhost:5555 in your browser"

# ============================================================================
# Database
# ============================================================================

migrate:  ## Run database migrations
	@echo "Running database migrations..."
	poetry run alembic upgrade head
	@echo "Migrations complete!"

migrate-auto:  ## Create a new migration (auto-detect changes)
	@read -p "Migration name: " name; \
	poetry run alembic revision --autogenerate -m "$$name"

migrate-create:  ## Create a new empty migration
	@read -p "Migration name: " name; \
	poetry run alembic revision -m "$$name"

migrate-down:  ## Rollback one migration
	@echo "Rolling back one migration..."
	poetry run alembic downgrade -1

migrate-history:  ## Show migration history
	poetry run alembic history --verbose

db-shell:  ## Open PostgreSQL shell
	@echo "Opening PostgreSQL shell..."
	docker exec -it pdc-postgres psql -U pdc_user -d pdc

db-reset:  ## Reset database (WARNING: Deletes all data!)
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker exec -it pdc-postgres psql -U pdc_user -d pdc -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
		$(MAKE) migrate; \
		echo "Database reset complete!"; \
	else \
		echo "Cancelled."; \
	fi

redis-shell:  ## Open Redis CLI
	@echo "Opening Redis CLI..."
	docker exec -it pdc-redis redis-cli

redis-flush:  ## Flush all Redis data (WARNING: Clears cache and queue!)
	@echo "WARNING: This will flush all Redis data (cache + queue)!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker exec -it pdc-redis redis-cli FLUSHALL; \
		echo "Redis flushed!"; \
	else \
		echo "Cancelled."; \
	fi

# ============================================================================
# Testing
# ============================================================================

test:  ## Run all tests
	@echo "Running all tests..."
	poetry run pytest -v

test-watch:  ## Run tests in watch mode
	@echo "Running tests in watch mode..."
	poetry run pytest-watch

test-unit:  ## Run unit tests only
	@echo "Running unit tests..."
	poetry run pytest -m unit -v

test-integration:  ## Run integration tests only
	@echo "Running integration tests..."
	poetry run pytest -m integration -v

test-e2e:  ## Run end-to-end tests only
	@echo "Running end-to-end tests..."
	poetry run pytest -m e2e -v

test-features:  ## Run ATDD acceptance tests (Gherkin features)
	@echo "Running acceptance tests..."
	poetry run pytest tests/features/ -v

test-cov:  ## Run tests with coverage report
	@echo "Running tests with coverage..."
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

test-cov-open:  ## Run tests with coverage and open report
	$(MAKE) test-cov
	@open htmlcov/index.html || xdg-open htmlcov/index.html

# ============================================================================
# Code Quality
# ============================================================================

lint:  ## Run all linters
	@echo "Running linters..."
	@$(MAKE) lint-ruff
	@$(MAKE) lint-mypy
	@echo "All linters passed!"

lint-ruff:  ## Run Ruff linter
	@echo "Running Ruff..."
	poetry run ruff check .

lint-mypy:  ## Run MyPy type checker
	@echo "Running MyPy..."
	poetry run mypy src/

format:  ## Format code with Ruff
	@echo "Formatting code..."
	poetry run ruff format .
	@echo "Code formatted!"

format-check:  ## Check if code is formatted
	@echo "Checking code format..."
	poetry run ruff format --check .

# ============================================================================
# Cleanup
# ============================================================================

clean:  ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleaned!"

clean-all:  ## Clean everything (including services)
	$(MAKE) clean
	$(MAKE) services-down
	@echo "All cleaned!"

# ============================================================================
# Utilities
# ============================================================================

shell:  ## Open Python shell with context loaded
	@echo "Opening Python shell..."
	poetry run ipython

env-check:  ## Check if .env file exists
	@if [ -f .env ]; then \
		echo "✓ .env file exists"; \
	else \
		echo "✗ .env file not found!"; \
		echo "  Run: cp .env.example .env"; \
		exit 1; \
	fi

health:  ## Check if all services are healthy
	@echo "Checking service health..."
	@echo "PostgreSQL:" && docker exec pdc-postgres pg_isready -U pdc_user || echo "  ✗ PostgreSQL not ready"
	@echo "Redis:" && docker exec pdc-redis redis-cli ping || echo "  ✗ Redis not ready"
	@echo "API:" && curl -s http://localhost:8000/v1/manage/health | jq . || echo "  ✗ API not responding"

logs-api:  ## Tail API logs
	tail -f logs/pdc.log

logs-celery:  ## Show Celery worker logs
	docker logs -f pdc-celery-worker || echo "Celery worker not running in Docker. Check terminal where you ran 'make worker'."

# ============================================================================
# Documentation
# ============================================================================

docs:  ## Open documentation
	@echo "Documentation is in the docs/ folder"
	@echo "  - docs/README.md: Navigation"
	@echo "  - docs/architecture/build-decisions.md: Architectural decisions"
	@echo "  - docs/features/roadmap.md: Feature roadmap"

# ============================================================================
# Quick Commands
# ============================================================================

up:  ## Quick start (services + API + worker in background)
	@$(MAKE) services
	@echo "Services started. Now run 'make api' and 'make worker' in separate terminals."

down:  ## Quick stop (stop all services)
	@$(MAKE) services-down

restart:  ## Quick restart
	@$(MAKE) down
	@$(MAKE) up

status:  ## Show status of all services
	@echo "Docker Services:"
	@docker-compose -f infrastructure/docker-compose.yml ps
	@echo ""
	@echo "Health Check:"
	@$(MAKE) health
