.PHONY: install test lint format dev run build docker-run deploy

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run black .

dev:
	uv run uvicorn app:create_app --factory --reload --port 8000

run:
	uv run uvicorn app:create_app --factory --host 0.0.0.0 --port $${PORT:-8000}

build:
	docker build -t ask-my-site .

docker-run: build
	docker run --rm -p 8000:8000 --env-file .env \
		-v $(PWD)/config:/app/config:ro \
		-v $(PWD)/context:/app/context:ro \
		ask-my-site

deploy:
	./deploy.sh
