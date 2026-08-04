FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app.py app.py
COPY src/ src/
COPY config/ config/
COPY context/ context/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# config/site.yaml and context/ can be bind-mounted at runtime (see `make docker-run`),
# overriding whatever was baked in from the COPY above - handy for local Docker testing.
# Cloud Run has no bind mounts, so a Cloud Run deploy relies on the baked-in copies instead.
#
# Shell form (not exec form) so $PORT expands - Cloud Run injects it and expects the
# container to listen on it (defaults to 8080 there; 8000 here matches `make docker-run`).
CMD uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}
