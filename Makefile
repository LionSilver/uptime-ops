.PHONY: lint test up down fmt validate

lint:
	cd app && python -m ruff check src tests

test:
	cd app && python -m pytest -q

up:
	docker compose up --build -d

down:
	docker compose down -v

fmt:
	terraform -chdir=terraform fmt

validate:
	terraform -chdir=terraform init -backend=false
	terraform -chdir=terraform validate
