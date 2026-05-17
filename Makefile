.PHONY: install run test lint typecheck migrate docker-up docker-down

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy app

migrate:
	alembic upgrade head

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v
