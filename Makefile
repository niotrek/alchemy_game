.PHONY: dev backend-dev mcp frontend-dev install test lint format type seed db-reset build clean help

PYTHON := uv run
NPM := npm --prefix frontend

help:
	@echo "Targets: dev, backend-dev, mcp, frontend-dev, install, test, lint, format, type, seed, db-reset, build, clean"

install:
	$(PYTHON) python -c "print('python deps already managed by uv sync')"
	$(NPM) install

dev:
	@echo "Starting backend on :8000 and frontend on :5173"
	@trap 'kill %1 %2 2>/dev/null' EXIT; \
		$(PYTHON) uvicorn apothecaria.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend 2>&1 | sed 's/^/[api] /' & \
		$(NPM) run dev 2>&1 | sed 's/^/[web] /' & \
		wait

backend-dev:
	$(PYTHON) uvicorn apothecaria.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend

mcp:
	$(PYTHON) python -m apothecaria.mcp.server

frontend-dev:
	$(NPM) run dev

build:
	$(NPM) run build

test:
	$(PYTHON) pytest

lint:
	$(PYTHON) ruff check backend
	$(NPM) run typecheck

format:
	$(PYTHON) ruff format backend

type:
	$(PYTHON) mypy backend/apothecaria

seed:
	$(PYTHON) python -m apothecaria.db.seed

db-reset:
	rm -f apothecaria.sqlite apothecaria.sqlite-journal
	$(MAKE) seed

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache *.egg-info __pycache__
	rm -rf frontend/node_modules frontend/dist frontend/.vite
	find . -type d -name __pycache__ -exec rm -rf {} +
