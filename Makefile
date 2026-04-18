.PHONY: help install dev test test-cov test-integration check-config clean

help:
	@echo "Available targets:"
	@echo "  install          - uv sync with dev dependencies"
	@echo "  dev              - start Flask development server"
	@echo "  test             - run unit tests"
	@echo "  test-cov         - run unit tests with coverage report"
	@echo "  test-integration - run integration tests (requires OLLAMA server)"
	@echo "  check-config     - validate environment configuration"
	@echo "  clean            - remove caches and coverage artifacts"

install:
	uv sync --dev

dev:
	uv run app.py

test:
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=term-missing

test-integration:
	uv run python tests/test_ollama_integration.py

check-config:
	uv run python validate_config.py

clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
