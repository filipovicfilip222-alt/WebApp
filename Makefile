#!/usr/bin/env bash
# Makefile for Studentska Platforma

.PHONY: help up down restart logs build clean migrate seed

help:
	@echo "Studentska Platforma — Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          Create .env from .env.example"
	@echo ""
	@echo "Docker:"
	@echo "  make up             Start all services"
	@echo "  make down           Stop all services"
	@echo "  make restart        Restart all services"
	@echo "  make build          Build all Docker images"
	@echo "  make logs           Show all service logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run Alembic migrations"
	@echo "  make seed           Seed database with dev data"
	@echo "  make db-shell       Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run backend tests"
	@echo "  make test-watch     Run tests in watch mode"
	@echo ""
	@echo "Development:"
	@echo "  make backend-shell  Open backend shell"
	@echo "  make frontend-shell Open frontend shell"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove all Docker containers and volumes"

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env file created from .env.example"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi

up:
	docker-compose up -d
	@echo "✅ All services started"
	@echo "📊 Services available at:"
	@echo "   - FastAPI: http://localhost:8000"
	@echo "   - Next.js: http://localhost:3000"
	@echo "   - Keycloak: http://localhost:8080"
	@echo "   - MinIO: http://localhost:9001"
	@echo "   - PostgreSQL: localhost:5432"

down:
	docker-compose down
	@echo "✅ All services stopped"

restart:
	docker-compose restart
	@echo "✅ All services restarted"

build:
	docker-compose build --no-cache
	@echo "✅ Docker images rebuilt"

logs:
	docker-compose logs -f

logs-backend:
	docker logs -f studentska_fastapi

logs-frontend:
	docker logs -f studentska_nextjs

logs-db:
	docker logs -f studentska_postgres

logs-redis:
	docker logs -f studentska_redis

logs-keycloak:
	docker logs -f studentska_keycloak

migrate:
	docker exec studentska_fastapi alembic upgrade head
	@echo "✅ Database migrations applied"

seed:
	docker exec studentska_fastapi python scripts/seed_dev_data.py
	@echo "✅ Database seeded with dev data"

db-shell:
	docker exec -it studentska_postgres psql -U postgres -d studentska_platforma

redis-shell:
	docker exec -it studentska_redis redis-cli

backend-shell:
	docker exec -it studentska_fastapi /bin/bash

frontend-shell:
	docker exec -it studentska_nextjs /bin/bash

test:
	docker exec studentska_fastapi pytest

test-watch:
	docker exec studentska_fastapi pytest --tb=short -v

test-coverage:
	docker exec studentska_fastapi pytest --cov=app --cov-report=html

lint-backend:
	docker exec studentska_fastapi bash -c "black app/ && isort app/"

lint-frontend:
	docker exec studentska_nextjs npm run lint

type-check-frontend:
	docker exec studentska_nextjs npm run type-check

clean:
	@echo "⚠️  This will remove all containers and volumes (data will be deleted)"
	@echo "Type 'yes' to confirm:"
	@read confirmation; \
	if [ "$$confirmation" = "yes" ]; then \
		docker-compose down -v; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

health:
	@echo "🏥 Health Check"
	@echo ""
	@echo "PostgreSQL:"
	@docker exec studentska_postgres psql -U postgres -c "SELECT 'OK';" 2>/dev/null && echo "  ✅ Running" || echo "  ❌ Not responding"
	@echo ""
	@echo "Redis:"
	@docker exec studentska_redis redis-cli ping 2>/dev/null && echo "  ✅ Running" || echo "  ❌ Not responding"
	@echo ""
	@echo "Keycloak:"
	@curl -s http://localhost:8080/health > /dev/null && echo "  ✅ Running" || echo "  ❌ Not responding"
	@echo ""
	@echo "FastAPI:"
	@curl -s http://localhost:8000/health > /dev/null && echo "  ✅ Running" || echo "  ❌ Not responding"
	@echo ""
	@echo "Next.js:"
	@curl -s http://localhost:3000 > /dev/null && echo "  ✅ Running" || echo "  ❌ Not responding"

.PHONY: logs logs-backend logs-frontend logs-db logs-redis logs-keycloak
.PHONY: backend-shell frontend-shell redis-shell test-coverage
.PHONY: lint-backend lint-frontend type-check-frontend health
