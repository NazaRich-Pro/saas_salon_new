.PHONY: help build up down logs restart migrate shell test clean init deploy monitor backup restore dev

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

init: ## Initialize project (first time setup)
	bash infra/scripts/init.sh

deploy: ## Deploy/update application
	bash infra/scripts/deploy.sh

build: ## Build all Docker images
	cd infra && docker compose build

up: ## Start all services
	cd infra && docker compose up -d

down: ## Stop all services
	cd infra && docker compose down

logs: ## Show logs from all services
	bash infra/scripts/logs.sh

restart: ## Restart all services
	cd infra && docker compose restart

monitor: ## Show system monitoring dashboard
	bash infra/scripts/monitor.sh

dev-up: ## Start local development environment
	docker compose -f docker-compose.dev.yml up -d

dev-down: ## Stop local development environment
	docker compose -f docker-compose.dev.yml down

migrate: ## Run Django migrations
	cd infra && docker compose exec api python manage.py migrate

makemigrations: ## Create Django migrations
	cd infra && docker compose exec api python manage.py makemigrations

shell: ## Open Django shell
	cd infra && docker compose exec api python manage.py shell

dbshell: ## Open PostgreSQL shell
	cd infra && docker compose exec postgres psql -U saas -d saas

superuser: ## Create Django superuser
	cd infra && docker compose exec api python manage.py createsuperuser

collectstatic: ## Collect Django static files
	cd infra && docker compose exec api python manage.py collectstatic --noinput

test-api: ## Run Django tests
	cd infra && docker compose exec api pytest

test-web: ## Run Next.js tests
	cd apps/web && npm test

lint-api: ## Lint Django code
	cd apps/api && black . && flake8

lint-web: ## Lint Next.js code
	cd apps/web && npm run lint

clean: ## Remove all containers, volumes, and images
	cd infra && docker compose down -v --rmi all

ps: ## Show running containers
	cd infra && docker compose ps

health: ## Check health of all services
	cd infra && docker compose ps && curl -f http://localhost:8000/api/health/ || echo "Services not healthy"

backup: ## Backup PostgreSQL database
	bash infra/scripts/backup.sh

restore: ## Restore PostgreSQL database (usage: make restore FILE=backup.sql.gz)
	bash infra/scripts/restore.sh $(FILE)


