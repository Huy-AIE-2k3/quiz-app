.PHONY: help dev dev-db stop-db test lint build clean

UV := $(HOME)/.local/bin/uv

help:
	@echo "=========================================================="
	@echo "MATHRIX Quiz System - Development Commands"
	@echo "=========================================================="
	@echo "  make dev       : Start Docker (DB + pgAdmin) + Backend + Frontend"
	@echo "  make dev-db    : Start only PostgreSQL & pgAdmin in Docker"
	@echo "  make stop-db   : Stop PostgreSQL & pgAdmin containers"
	@echo "  make test      : Run both Backend (pytest) and Frontend (vitest) tests"
	@echo "  make lint      : Run linters (ruff, mypy, tsc)"
	@echo "  make build     : Build Frontend for production"
	@echo "  make clean     : Clean up build artifacts and temporary caches"
	@echo "=========================================================="

dev:
	./scripts/dev.sh

dev-db:
	docker compose up -d
	@echo "PostgreSQL running on localhost:5432"
	@echo "pgAdmin running on http://localhost:5050 (admin@mathrix.edu.vn / admin)"

stop-db:
	docker compose down

test:
	@echo "=== Running Backend Tests (pytest) ==="
	cd backend && $(UV) run pytest -v
	@echo "=== Running Frontend Tests (vitest) ==="
	cd frontend && npm test

lint:
	@echo "=== Running Backend Linter (ruff) ==="
	cd backend && $(UV) run ruff check app tests
	@echo "=== Running Backend Typechecker (mypy) ==="
	cd backend && $(UV) run mypy app
	@echo "=== Running Frontend Typechecker (tsc) ==="
	cd frontend && npm run build

build:
	cd frontend && npm run build

clean:
	rm -rf frontend/dist frontend/.vite
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
