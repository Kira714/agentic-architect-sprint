.PHONY: help build up down logs restart clean db-backup db-restore

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-db: ## View database logs
	docker-compose logs -f postgres

restart: ## Restart all services
	docker-compose restart

restart-backend: ## Restart backend only
	docker-compose restart backend

clean: ## Stop services and remove volumes
	docker-compose down -v

rebuild: ## Rebuild and restart services
	docker-compose up -d --build

dev: ## Start in development mode with hot reload
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod: ## Start in production mode
	docker-compose -f docker-compose.prod.yml up -d

db-backup: ## Backup PostgreSQL database
	docker-compose exec postgres pg_dump -U cerina cerina_foundry > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to backup_*.sql"

db-restore: ## Restore PostgreSQL database (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T postgres psql -U cerina cerina_foundry < $(FILE)

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U cerina -d cerina_foundry

db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker volume rm airbyte-common-handler_postgres_data 2>/dev/null || true
	docker-compose up -d

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

test: ## Run tests (if available)
	docker-compose exec backend python -m pytest

status: ## Show status of all services
	docker-compose ps





