.PHONY: test test-unit test-quick lint typecheck ci release fmt

test:
	uv run pytest tests/ -v --cov=scripts --cov-report=term-missing

test-unit:
	uv run pytest tests/ -v -m unit --cov=scripts --cov-report=term-missing

test-quick:
	uv run pytest tests/ -v --no-cov

lint:
	uv run ruff check scripts/ tests/
	uv run ruff format --check scripts/ tests/

fmt:
	uv run ruff check --fix scripts/ tests/
	uv run ruff format scripts/ tests/

typecheck:
	uv run pyright scripts/

ci: lint typecheck test

release:
	@echo "=== 发布流程 ==="
	@echo "1. 确认 pyproject.toml 版本号已更新"
	@python3 -c "import tomllib; v=tomllib.load(open('pyproject.toml','rb'))['project']['version']; print(f'  当前版本: {v}')"
	@echo "2. git tag v$$(python3 -c \"import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\")"
	@echo "3. git push origin main --tags"
	@echo "4. 在 GitHub 上创建 Release"
