.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help setup check check-nospend models policy lint test docker-build up down logs hermes-init hermes-doctor hermes-shell clean

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

setup: ## Create .venv and install all dependencies (uv); create .env from the example
	$(UV) sync --all-groups
	@mkdir -p data hermes/home
	@test -f .env || (cp .env.example .env && echo ">> .env created from .env.example — fill in your keys")

setup-data: ## Also install the synthetic-document toolchain (needs pango libs; see pyproject)
	$(UV) sync --all-groups --extra data

check: ## Verify keys, policy/locale, models (incl. one Omni vision call), Telegram bot, Tavily
	$(UV) run kin check

check-nospend: ## Same as check, without paid calls
	$(UV) run kin check --no-spend

models: ## List Nemotron model IDs visible to this key
	$(UV) run kin models

policy: ## Print and validate the policy matrix
	$(UV) run kin policy

lint: ## Ruff
	$(UV) run ruff check .
	$(UV) run ruff format --check .

test: ## Pytest
	$(UV) run pytest -q

docker-build: ## Build kin and hermes images
	docker compose build

up: ## Start kin + hermes gateway (first hermes start installs Hermes into ./hermes/home)
	docker compose up -d

down: ## Stop containers
	docker compose down

logs: ## Follow logs
	docker compose logs -f

hermes-init: ## Seed ./hermes/home/config.yaml from the template (no-op if it exists)
	@mkdir -p hermes/home
	@test -f hermes/home/config.yaml || (cp hermes/config.yaml hermes/home/config.yaml && echo ">> seeded hermes/home/config.yaml")

hermes-doctor: ## Run `hermes doctor` inside the container
	docker compose run --rm hermes doctor

hermes-shell: ## Interactive shell in the hermes container (hermes on PATH)
	docker compose run --rm hermes shell

clean: ## Remove venv and caches
	rm -rf .venv .pytest_cache .ruff_cache
