.PHONY: install run test lint typecheck migrate setup-xrechnung-validator setup-spanish-sif-assets docker-up docker-down docker-multiregion-up docker-multiregion-down smoke-multiregion

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

setup-xrechnung-validator:
	scripts/setup_xrechnung_validator.sh

setup-spanish-sif-assets:
	scripts/setup_spanish_sif_assets.sh

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v

docker-multiregion-up:
	docker-compose -f docker-compose.multi-region.yml up --build

docker-multiregion-down:
	docker-compose -f docker-compose.multi-region.yml down -v

smoke-multiregion:
	scripts/smoke_multi_region.sh
