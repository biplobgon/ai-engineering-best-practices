.PHONY: help install sync lint fmt test up down eval docs clean repl

help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║ ai-engineering-best-practices — Development Commands      ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install          Install dependencies (uv sync)"
	@echo "  make sync             Sync lock file (uv sync)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff checks + mypy"
	@echo "  make fmt              Format code (black + ruff)"
	@echo "  make check            Lint without fixing"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run pytest (unit + integration)"
	@echo "  make test-fast        Run fast tests only (no @slow)"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make eval             Run eval suite (requires APIs)"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up               Start Docker services (redis, postgres, jaeger, mlflow)"
	@echo "  make down             Stop Docker services"
	@echo "  make logs             Tail Docker logs"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Build mkdocs site"
	@echo "  make docs-serve       Serve docs locally on :8000"
	@echo ""
	@echo "Development:"
	@echo "  make repl             Start Python REPL"
	@echo "  make clean            Remove artifacts, cache, venv"
	@echo ""
	@echo "Examples:"
	@echo "  make install && make up      Setup environment"
	@echo "  make lint && make test       Full CI workflow locally"
	@echo "  make docs-serve              Read docs while coding"

install:
	uv sync --all-extras

sync:
	uv sync

lint:
	ruff check . --fix
	black --check .
	mypy core/

fmt:
	black .
	ruff check . --fix

check:
	ruff check .
	black --check .
	mypy core/

test:
	pytest -v tests/ core/

test-fast:
	pytest -v tests/ core/ -m "not slow and not requires_api"

test-cov:
	pytest --cov=core --cov-report=html --cov-report=term tests/ core/

eval:
	pytest -v tests/ -m "eval"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

docs:
	mkdocs build

docs-serve:
	mkdocs serve

repl:
	uv run python

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build *.egg-info
	rm -rf .venv

pre-commit:
	pre-commit install
	pre-commit run --all-files

version:
	@uv --version
	@python --version
	@ruff --version
	@pytest --version
