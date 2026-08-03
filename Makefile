.PHONY: install test lint dev run build docker-run

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

dev:
	PYTHONPATH=src uv run uvicorn api.app:create_app --factory --reload --port 8000

run:
	PYTHONPATH=src uv run uvicorn api.app:create_app --factory --host 0.0.0.0 --port $${PORT:-8000}

build:
	docker build -t ask-my-site .

docker-run: build
	docker run --rm -p 8000:8000 --env-file .env \
		-v $(PWD)/config:/app/config:ro \
		-v $(PWD)/context:/app/context:ro \
		ask-my-site
