.PHONY: dev stop dev-bg logs test lint format migrate migrate-new migrate-down \
        sdk-test-python sdk-test-ts sdk-test openapi clean load-test ci \
        website-dev website-build website-lint \
        benchmark benchmark-locomo benchmark-msc benchmark-latency benchmark-tamper benchmark-quick

SHELL := /bin/bash

# ─── Development ───────────────────────────────
dev:
	docker-compose up --build

stop:
	docker-compose down

dev-bg:
	docker-compose up --build -d

logs:
	docker-compose logs -f kyros-server

# ─── Server ────────────────────────────────────
test:
	(cd server && uv run pytest -v --cov=kyros --cov-report=term-missing)

lint:
	(cd server && uv run ruff check . && uv run mypy kyros/)

format:
	(cd server && uv run ruff format . && uv run ruff check --fix .)

# ─── Database ──────────────────────────────────
migrate:
	(cd server && uv run alembic upgrade head)

migrate-new:
	@if [ -z "$(msg)" ]; then \
		echo "Usage: make migrate-new msg='your migration message'"; \
		exit 1; \
	fi
	(cd server && uv run alembic revision --autogenerate -m "$(msg)")

migrate-down:
	(cd server && uv run alembic downgrade -1)

# ─── SDK ───────────────────────────────────────
sdk-test-python:
	(cd sdks/python && uv run pytest -v)

sdk-test-ts:
	(cd sdks/typescript && npm test -- --passWithNoTests)

sdk-test: sdk-test-python sdk-test-ts

# ─── OpenAPI ───────────────────────────────────
openapi:
	(cd server && uv run python -c \
		"from kyros.main import app; import json; print(json.dumps(app.openapi(), indent=2))") \
		> docs/openapi.json
	@echo "OpenAPI spec written to docs/openapi.json"

# ─── Cleanup ───────────────────────────────────
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete

# ─── Load Testing ─────────────────────────────
load-test:
	(cd server && uv run locust -f tests/load/locustfile.py --host=http://localhost:8000)

# ─── Seed Data ────────────────────────────────
seed:
	docker-compose exec kyros-server python tests/seed_data.py

# ─── Benchmarks ───────────────────────────────
# ─── Benchmarks ───────────────────────────────────────────────────────────────
# Data files are mounted from your local machine into the container at /data/
# Override BENCHMARK_DATA_DIR in .env or on the command line if your files
# are in a different folder.
#
# Usage:
#   make benchmark-quick
#   make benchmark-locomo
#   make benchmark-msc
#   make benchmark-latency
#   make benchmark-tamper
#   make benchmark-all

benchmark-quick:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--locomo /data/locomo10.json \
		--msc    /data/msc_personas_all.json \
		--quick

benchmark-locomo:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--locomo /data/locomo10.json \
		--only locomo

benchmark-msc:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--msc /data/msc_personas_all.json \
		--only msc

benchmark-latency:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--only latency --scales 1000 10000

benchmark-tamper:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--only tamper

benchmark-all:
	docker-compose exec kyros-server python tests/benchmarks/run_local.py \
		--locomo /data/locomo10.json \
		--msc    /data/msc_personas_all.json

# ─── Full CI locally ──────────────────────────
ci: lint test sdk-test
	@echo "✅ All checks passed"

# ─── Website ──────────────────────────────────
website-dev:
	@echo "Run manually: cd website && npm run dev"

website-build:
	(cd website && npm run build)

website-lint:
	(cd website && npm run lint)
