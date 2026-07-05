.PHONY: install run run-full test test-e2e lint format

install:
	uv sync

run:
	uv run fastapi dev app/main.py

run-full:
	docker compose up --build

test:
	uv run pytest

test-e2e:
	uv run pytest -m e2e

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .
