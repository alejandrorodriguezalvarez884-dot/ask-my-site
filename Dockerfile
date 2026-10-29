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

# Local Docker runs bind-mount config/ and context/ (see `make docker-run`). On Cloud Run
# CONTENT_BUCKET is set and the app downloads both from Cloud Storage at startup instead;
# .gcloudignore keeps the real files out of the image, so the COPYs above only carry
# site.example.yaml and context/.gitkeep there.
#
# Shell form (not exec form) so $PORT expands - Cloud Run injects it and expects the
# container to listen on it (defaults to 8080 there; 8000 here matches `make docker-run`).
CMD uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}
