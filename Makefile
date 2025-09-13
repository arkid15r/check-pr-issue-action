.PHONY: help install install-dev test test-cov lint format check clean pre-commit

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=90

lint: ## Run linting
	ruff check .

format: ## Format code
	ruff format .

check: lint test ## Run linting and tests

clean: ## Clean up generated files
	rm -rf .coverage htmlcov/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files
