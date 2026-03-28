.PHONY: help install lint format type-check test test-smoke test-report parse-har sync-repos plan-har render-acceptance clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	uv sync --all-extras
	uv run pre-commit install

lint: ## Run linting
	uv run ruff check src/ tests/ api/ testdata/
	uv run ruff format --check src/ tests/ api/ testdata/

format: ## Format code
	uv run ruff check --fix src/ tests/ api/ testdata/
	uv run ruff format src/ tests/ api/ testdata/

type-check: ## Run type checking
	uv run pyright src/

test: ## Run all tests
	uv run pytest tests/

test-smoke: ## Run smoke tests only
	uv run pytest tests/ -m smoke

test-report: ## Run tests with Allure report
	uv run pytest tests/ --alluredir=allure-results
	@echo "Run 'allure serve allure-results' to view report"

parse-har: ## Parse a HAR file (usage: make parse-har FILE=path/to/file.har)
	uv run python -m sisyphus_auto_flow.parsers.har_parser $(FILE)

sync-repos: ## Sync backend source repositories (usage: make sync-repos RELEASE=release_6.2.x)
	@bash .claude/scripts/sync_release_repos.sh $(or $(RELEASE),release_6.2.x)

plan-har: ## Generate workflow manifest (usage: make plan-har FILE=.data/parsed/parsed_requests.json RELEASE=release_6.2.x OUTPUT=.data/parsed/file.workflow.json)
	@bash .claude/scripts/plan_har_workflow.sh $(FILE) $(or $(RELEASE),release_6.2.x) $(OUTPUT)

render-acceptance: ## Render acceptance checklist (usage: make render-acceptance MANIFEST=.data/parsed/file.workflow.json)
	@bash .claude/scripts/render_acceptance_summary.sh $(MANIFEST)

clean: ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache .ruff_cache allure-results allure-report dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .data/parsed/* && touch .data/parsed/.gitkeep
