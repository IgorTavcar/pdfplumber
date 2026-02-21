.PHONY: sync tests lint format examples build

sync:
	uv sync --all-extras

tests:
	uv run pytest -n auto
	uv run coverage html

check-ruff:
	uv run ruff check pdfplumber tests
	uv run ruff format --check pdfplumber tests

check-mypy:
	uv run mypy pdfplumber

lint: check-ruff check-mypy

format:
	uv run ruff format pdfplumber tests
	uv run ruff check --fix pdfplumber tests

examples:
	uv run nbexec examples/notebooks

build:
	uv build
